
import argparse
import os

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.callbacks import EvalCallback, BaseCallback, CallbackList

from env import TowerDefenseEnv


def make_env():
    def _init():
        env = TowerDefenseEnv()
        env = Monitor(env)
        return env
    return _init


def linear_schedule(initial_value):
    def func(progress_remaining):
        return progress_remaining * initial_value
    return func


class EntropyDecayCallback(BaseCallback):

    def __init__(self, initial_ent_coef, final_ent_coef, total_timesteps, verbose=0):
        super().__init__(verbose)
        self.initial_ent_coef = initial_ent_coef
        self.final_ent_coef = final_ent_coef
        self.total_timesteps = total_timesteps

    def _on_step(self):
        progress = min(self.num_timesteps / self.total_timesteps, 1.0)
        new_ent_coef = self.initial_ent_coef + progress * (self.final_ent_coef - self.initial_ent_coef)
        self.model.ent_coef = new_ent_coef
        return True


def main(total_timesteps, model_path, log_dir, ent_coef, n_envs, final_ent_coef, use_lr_schedule):
    os.makedirs(os.path.dirname(model_path) or ".", exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

    train_env = DummyVecEnv([make_env() for _ in range(n_envs)])
    eval_env = DummyVecEnv([make_env()])

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=os.path.dirname(model_path) or ".",
        log_path=log_dir,
        eval_freq=10_000,
        n_eval_episodes=10,
        deterministic=True,
    )

    entropy_decay_callback = EntropyDecayCallback(
        initial_ent_coef=ent_coef,
        final_ent_coef=final_ent_coef,
        total_timesteps=total_timesteps,
    )
    callback = CallbackList([eval_callback, entropy_decay_callback])

    learning_rate = linear_schedule(3e-4) if use_lr_schedule else 3e-4

    model = PPO(
        "MlpPolicy",
        train_env,
        verbose=1,
        learning_rate=learning_rate,
        ent_coef=ent_coef,
        policy_kwargs=dict(net_arch=[128, 128]),
        tensorboard_log=os.path.join(log_dir, "tensorboard"),
    )

    model.learn(total_timesteps=total_timesteps, callback=callback)
    model.save(model_path)
    print(f"\nKesz. Modell mentve ide: {model_path}.zip")
    print(f"A legjobb (kiertekeles alapjan) modell: "
          f"{os.path.join(os.path.dirname(model_path) or '.', 'best_model.zip')}")
    print(f"\nTensorBoard: tensorboard --logdir {os.path.join(log_dir, 'tensorboard')}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=500_000,
                         help="Osszes tanitasi lepes (frame-skip-elt env.step() hivas)")
    parser.add_argument("--model-path", type=str, default="models/ppo_tower_defense")
    parser.add_argument("--log-dir", type=str, default="logs")
    parser.add_argument("--ent-coef", type=float, default=0.01,
                         help="Entropia-bonusz: nagyobb ertek = tovabbi 'kiserletezes' "
                              "osztonzese tanitas kozben (alapertelmezett SB3-ban: 0.0)")
    parser.add_argument("--n-envs", type=int, default=8,
                         help="Parhuzamos kornyezetek szama tanitaskor -- tobb env "
                              "stabilabb (kisebb varianciaju) tanulasi gradienst ad")
    parser.add_argument("--final-ent-coef", type=float, default=0.0,
                         help="Az entropia-bonusz erteke, amire a tanitas vegere "
                              "linearisan lecsokken a kezdeti --ent-coef ertekrol "
                              "(alapertelmezett: 0.0 -- a tanitas vegen mar ne "
                              "'kiserletezzen' az ugynok)")
    parser.add_argument("--no-lr-schedule", action="store_true",
                         help="Ha megadod, a tanulasi rata NEM csokken a tanitas "
                              "soran, hanem allando marad (SB3 alapertelmezett: 3e-4)")
    args = parser.parse_args()

    main(args.timesteps, args.model_path, args.log_dir, args.ent_coef, args.n_envs,
         args.final_ent_coef, not args.no_lr_schedule)
