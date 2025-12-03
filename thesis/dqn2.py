import pdb
import cv2
import sys
import os

# sys.path.append("game/")
os.chdir(r"D:/workspace-lilyco/lilyco_storybook/thesis")
sys.path.insert(0, r"D:/workspace-lilyco/lilyco_storybook/thesis/game/")
import wrapped_flappy_bird as game
import random
import numpy as np
from collections import deque
import torch
from torch.autograd import Variable
import torch.nn as nn
from torch.utils.tensorboard import SummaryWriter

GAME = "bird"  # the name of the game being played for log files
ACTIONS = 2  # number of valid actions
GAMMA = 0.99  # decay rate of past observations
OBSERVE = (
    1000  # timesteps to observe before training (reduced to start training earlier)
)
EXPLORE = (
    100000  # frames over which to anneal epsilon (shorter so epsilon decays faster)
)
FINAL_EPSILON = 0.0001  # final value of epsilon
INITIAL_EPSILON = 1  # starting value of epsilon
# during random exploration, prefer doing nothing to reduce ceiling hits
EXPLORATION_NOOP_PROB = (
    0.9  # probability of choosing 'do nothing' when exploring (more no-op)
)
REPLAY_MEMORY = 50000  # number of previous transitions to remember
BATCH_SIZE = 32  # size of minibatch
FRAME_PER_ACTION = 1
UPDATE_TIME = 50
width = 80
height = 80


def preprocess(observation):
    observation = cv2.cvtColor(cv2.resize(observation, (80, 80)), cv2.COLOR_BGR2GRAY)
    ret, observation = cv2.threshold(observation, 1, 255, cv2.THRESH_BINARY)
    return np.reshape(observation, (1, 80, 80))


class DeepNetWork(nn.Module):
    def __init__(
        self,
    ):
        super(DeepNetWork, self).__init__()
        self.conv1 = nn.Sequential(
            nn.Conv2d(
                in_channels=4, out_channels=32, kernel_size=8, stride=4, padding=2
            ),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2),
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(
                in_channels=32, out_channels=64, kernel_size=4, stride=2, padding=1
            ),
            nn.ReLU(inplace=True),
        )
        self.conv3 = nn.Sequential(
            nn.Conv2d(
                in_channels=64, out_channels=64, kernel_size=3, stride=1, padding=1
            ),
            nn.ReLU(inplace=True),
        )
        self.fc1 = nn.Sequential(nn.Linear(1600, 256), nn.ReLU())
        self.out = nn.Linear(256, 2)

    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = x.view(x.size(0), -1)
        x = self.fc1(x)
        return self.out(x)


class BrainDQNMain(object):
    def save(self):
        print("save model param")
        torch.save(self.Q_net.state_dict(), "params3.pth")
        # also save a full checkpoint for reliable resume
        self.save_checkpoint("checkpoint.pth")
        self.writer.flush()

    def save_checkpoint(self, path="checkpoint.pth"):
        tmp = path + ".tmp"
        checkpoint = {
            "model": self.Q_net.state_dict(),
            "target_model": self.Q_netT.state_dict(),
            "optimizer": self.optimizer.state_dict(),
            "timeStep": self.timeStep,
            "epsilon": self.epsilon,
            "best_reward": getattr(self, "best_reward", float("-inf")),
            # replay buffer saving is optional due to size
            # 'replay': list(self.replayMemory)
        }
        torch.save(checkpoint, tmp)
        try:
            os.replace(tmp, path)
        except Exception:
            # fallback
            os.remove(path) if os.path.exists(path) else None
            os.rename(tmp, path)

    def load_checkpoint(self, path="checkpoint.pth"):
        if os.path.exists(path):
            print("load checkpoint", path)
            ck = torch.load(path)
            self.Q_net.load_state_dict(ck["model"])
            self.Q_netT.load_state_dict(ck.get("target_model", ck["model"]))
            if "optimizer" in ck:
                try:
                    self.optimizer.load_state_dict(ck["optimizer"])
                except Exception:
                    pass
            self.timeStep = ck.get("timeStep", self.timeStep)
            self.epsilon = ck.get("epsilon", self.epsilon)
            self.best_reward = ck.get("best_reward", float("-inf"))
            # replay restoration omitted by default

    def load(self):
        # prefer checkpoint that contains optimizer and meta state
        # if running in play mode prefer the best saved params
        if getattr(self, "play", False):
            if os.path.exists("params_best.pth"):
                print("load best model params_best.pth")
                self.Q_net.load_state_dict(torch.load("params_best.pth"))
                self.Q_netT.load_state_dict(torch.load("params_best.pth"))
                return
        if os.path.exists("checkpoint.pth"):
            self.load_checkpoint("checkpoint.pth")
        elif os.path.exists("params3.pth"):
            print("load model param")
            self.Q_net.load_state_dict(torch.load("params3.pth"))
            self.Q_netT.load_state_dict(torch.load("params3.pth"))

    def __init__(self, actions):
        self.replayMemory = deque()  # init some parameters
        self.timeStep = 0
        # default: training mode
        self.play = False
        self.epsilon = INITIAL_EPSILON
        # probability to choose no-op (index 0) during random exploration
        self.exploration_noop_prob = EXPLORATION_NOOP_PROB
        self.actions = actions
        self.Q_net = DeepNetWork()
        self.Q_netT = DeepNetWork()
        self.loss_func = nn.MSELoss()
        # increase LR slightly to speed learning on CPU (monitor for instability)
        LR = 5e-4
        self.optimizer = torch.optim.Adam(self.Q_net.parameters(), lr=LR)
        # attempt to load checkpoint after optimizer exists
        self.load()
        self.writer = SummaryWriter("runs/dqn_experiment")
        # track cumulative reward for current episode
        self.episode_reward = 0.0
        # best reward observed (for saving best model)
        self.best_reward = getattr(self, "best_reward", float("-inf"))

    def train(self):  # Step 1: obtain random minibatch from replay memory
        # avoid sampling more elements than available
        if len(self.replayMemory) < BATCH_SIZE:
            return
        minibatch = random.sample(self.replayMemory, BATCH_SIZE)
        state_batch = [data[0] for data in minibatch]
        action_batch = [data[1] for data in minibatch]
        reward_batch = [data[2] for data in minibatch]
        nextState_batch = [data[3] for data in minibatch]  # Step 2: calculate y
        y_batch = np.zeros([BATCH_SIZE, 1])
        nextState_batch = np.array(nextState_batch)  # print("train next state shape")
        # print(nextState_batch.shape)
        nextState_batch = torch.Tensor(nextState_batch)
        action_batch = np.array(action_batch)
        index = action_batch.argmax(axis=1)
        # print("action " + str(index))
        index = np.reshape(index, [BATCH_SIZE, 1])
        action_batch_tensor = torch.LongTensor(index)
        QValue_batch = self.Q_netT(nextState_batch)
        QValue_batch = QValue_batch.detach().numpy()

        for i in range(0, BATCH_SIZE):
            terminal = minibatch[i][4]
            if terminal:
                y_batch[i][0] = reward_batch[i]
            else:
                # 这里的QValue_batch[i]为数组，大小为所有动作集合大小，QValue_batch[i],代表
                # 做所有动作的Q值数组，y计算为如果游戏停止，y=rewaerd[i],如果没停止，则y=reward[i]+gamma*np.max(Qvalue[i])
                # 代表当前y值为当前reward+未来预期最大值*gamma(gamma:经验系数)
                y_batch[i][0] = reward_batch[i] + GAMMA * np.max(QValue_batch[i])

        y_batch = np.array(y_batch)
        y_batch = np.reshape(y_batch, [BATCH_SIZE, 1])
        state_batch_tensor = Variable(torch.Tensor(state_batch))
        y_batch_tensor = Variable(torch.Tensor(y_batch))
        y_predict = self.Q_net(state_batch_tensor).gather(1, action_batch_tensor)
        loss = self.loss_func(y_predict, y_batch_tensor)
        # print("loss is " + str(loss))
        self.writer.add_scalar("loss", loss.item(), self.timeStep)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        if self.timeStep % UPDATE_TIME == 0:
            self.Q_netT.load_state_dict(self.Q_net.state_dict())
            self.save()

    def setPerception(self, nextObservation, action, reward, terminal):
        newState = np.append(self.currentState[1:, :, :], nextObservation, axis=0)
        self.replayMemory.append(
            (self.currentState, action, reward, newState, terminal)
        )
        if len(self.replayMemory) > REPLAY_MEMORY:
            self.replayMemory.popleft()

        # log step reward
        try:
            self.writer.add_scalar("reward/step", float(reward), self.timeStep)
        except Exception:
            pass

        # accumulate episode reward
        self.episode_reward += float(reward)

        # Print current reward and cumulative episode reward for debugging
        try:
            print(
                f"STEP {self.timeStep} REWARD {float(reward)} CUM_REWARD {self.episode_reward}"
            )
        except Exception:
            pass

        # Train the network
        # Only train when not in play mode
        if (not getattr(self, "play", False)) and self.timeStep > OBSERVE:
            self.train()

        # if episode ended, log episode reward and reset
        if terminal:
            # capture episode reward before resetting
            ep_reward = float(self.episode_reward)
            try:
                self.writer.add_scalar("reward/episode", ep_reward, self.timeStep)
            except Exception:
                pass
            # save best model if improved
            try:
                if ep_reward > getattr(self, "best_reward", float("-inf")):
                    print(
                        "New best episode reward",
                        ep_reward,
                        "-> saving best model",
                    )
                    self.best_reward = ep_reward
                    torch.save(self.Q_net.state_dict(), "params_best.pth")
                    # also save a checkpoint snapshot
                    self.save_checkpoint("checkpoint_best.pth")
            except Exception:
                pass

            # print episode summary for visibility (use captured value)
            try:
                print(
                    f"Episode ended: reward={ep_reward}, best_reward={getattr(self,'best_reward',float('-inf'))}"
                )
            except Exception:
                pass

            # reset episode reward after printing
            self.episode_reward = 0.0

        # log epsilon occasionally to reduce IO
        if self.timeStep % 100 == 0:
            try:
                self.writer.add_scalar("epsilon", float(self.epsilon), self.timeStep)
            except Exception:
                pass

        state = ""
        if self.timeStep <= OBSERVE:
            state = "observe"
        elif self.timeStep > OBSERVE and self.timeStep <= OBSERVE + EXPLORE:
            state = "explore"
        else:
            state = "train"
        if self.timeStep % 100 == 0:
            print(
                "TIMESTEP", self.timeStep, "/ STATE", state, "/ EPSILON", self.epsilon
            )
        self.currentState = newState
        self.timeStep += 1

    def getAction(self):
        currentState = torch.Tensor([self.currentState])
        QValue = self.Q_net(currentState)[0]
        action = np.zeros(self.actions)
        # force deterministic greedy policy in play mode
        if getattr(self, "play", False):
            self.epsilon = 0.0
        if self.timeStep % FRAME_PER_ACTION == 0:
            if random.random() <= self.epsilon:
                # weighted random: prefer no-op to reduce ceiling hits
                if random.random() < getattr(
                    self, "exploration_noop_prob", EXPLORATION_NOOP_PROB
                ):
                    action_index = 0
                else:
                    action_index = 1
                # debug print
                print("choose random action " + str(action_index))
                action[action_index] = 1
            else:
                action_index = np.argmax(QValue.detach().numpy())
                print("choose qnet value action " + str(action_index))
                action[action_index] = 1
        else:
            action[0] = 1  # do nothing

        # log max Q-value occasionally
        try:
            max_q = float(QValue.detach().max().item())
            if self.timeStep % 50 == 0:
                self.writer.add_scalar("q_value/max", max_q, self.timeStep)
        except Exception:
            pass

        # change episilon
        if self.epsilon > FINAL_EPSILON and self.timeStep > OBSERVE:
            self.epsilon -= (INITIAL_EPSILON - FINAL_EPSILON) / EXPLORE
        return action

    def setInitState(self, observation):
        self.currentState = np.stack(
            (observation, observation, observation, observation), axis=0
        )
        print(self.currentState.shape)


if __name__ == "__main__":
    # Step 1: init BrainDQN
    actions = 2
    # support CLI flags: 'play' and '--reset-meta'
    flags = set(arg.lower() for arg in sys.argv[1:])
    play_mode = "play" in flags
    reset_meta = "--reset-meta" in flags or "reset-meta" in flags
    if play_mode:
        print("Starting in PLAY mode: loading best model and disabling training")
        brain = BrainDQNMain(actions)
        brain.play = True
        brain.epsilon = 0.0
        # reload to prefer params_best.pth when available
        brain.load()
    else:
        brain = BrainDQNMain(actions)
    # apply meta-reset if requested (keeps loaded weights but resets timers/epsilon/best)
    if reset_meta:
        print("Resetting meta-state: timeStep, epsilon, best_reward")
        brain.timeStep = 0
        brain.epsilon = INITIAL_EPSILON
        brain.best_reward = float("-inf")

    flappyBird = game.GameState()  # Step 3: play game
    # Step 3.1: obtain init state
    action0 = np.array([1, 0])  # do nothing
    observation0, reward0, terminal = flappyBird.frame_step(action0)
    observation0 = cv2.cvtColor(cv2.resize(observation0, (80, 80)), cv2.COLOR_BGR2GRAY)
    ret, observation0 = cv2.threshold(observation0, 1, 255, cv2.THRESH_BINARY)
    brain.setInitState(observation0)
    print(brain.currentState.shape)  # Step 3.2: run the game

    try:
        while 1 != 0:
            action = brain.getAction()
            nextObservation, reward, terminal = flappyBird.frame_step(action)
            nextObservation = preprocess(nextObservation)
            brain.setPerception(nextObservation, action, reward, terminal)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        try:
            if not getattr(brain, "play", False):
                print("Saving checkpoint...")
                brain.save_checkpoint("checkpoint.pth")
            else:
                print("Play mode detected — not saving checkpoint.")
        except Exception:
            pass
        try:
            brain.writer.close()
        except Exception:
            pass
    except Exception as e:
        print("Exception occurred:", e)
        try:
            if not getattr(brain, "play", False):
                brain.save_checkpoint("checkpoint.pth")
        except Exception:
            pass
        try:
            brain.writer.close()
        except Exception:
            pass
