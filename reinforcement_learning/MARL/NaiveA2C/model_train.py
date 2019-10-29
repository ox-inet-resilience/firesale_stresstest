import matplotlib.pyplot as plt
import numpy as np

from reinforcement_learning.gym_env import RLModelEnv
from reinforcement_learning.MARL.NaiveA2C.ddpg_agent import Agent
from reinforcement_learning.MARL.NaiveA2C.util import setup_matplotlib, plot_custom_errorbar_plot
from contracts import Tradable


def MA_obs_to_bank_obs(obs, bank):
    bank_obs = obs[bank.get_name()]
    # print(f'BANK OBS of {bank.BankName}', bank_obs)
    cb_price, gb_price = bank_obs[0][1], bank_obs[0][2]
    leverage = bank_obs[3]
    return np.asarray([cb_price, gb_price, leverage])


RLagent_dict = {}
env = RLModelEnv()
bank_names = 'AT01 AT02 BE03 BE04 DK05 DK06 DK07 FI08 FR09 FR10 FR11 FR12 FR13 FR14 DE15 DE16 DE17 DE18 DE19 DE20 DE21 DE22 HU23 IE24 IE25 IT26 IT27 IT28 IT29 NL30 NL31 NL32 NL33 NO34 PL35 PL36 ES37 ES38 ES39 ES40 SE41 SE42 SE43 SE44 UK45 UK46 UK47 UK48'.split()

for idx, name in enumerate(bank_names):
    agent = Agent(state_size=3, action_size=2, random_seed=idx, name=name)
    RLagent_dict[name] = agent

average_lifespans = []
for episode in range(1000):

    if episode == 0 or episode % 100 == 0:
        print(f'=========================================Episode {episode}===============================================')
    current_obs = env.reset()
    play, max_play = 0, 15
    num_default = []
    while play < max_play:
        actions = {}
        for bank_name, bank in env.allAgents_dict.items():
            if not bank.alive:
                continue
            if episode % 100 == 0:
                CB_qty = bank.get_ledger().get_asset_valuation_of(Tradable, 1)
                GB_qty = bank.get_ledger().get_asset_valuation_of(Tradable, 2)
                equity = bank.get_ledger().get_equity_valuation()
                lev_ratio_percent = bank.leverageConstraint.get_leverage() * 100
                print(f'Round {play}. Bank {bank_name}, CB: {int(CB_qty)}, GB: {int(GB_qty)}, EQUITY: {int(equity)}, LEV: {int(lev_ratio_percent)}%')
            # conversion
            my_obs = MA_obs_to_bank_obs(current_obs, bank)
            current_obs[bank_name] = my_obs
            # choose action
            action = RLagent_dict[bank_name].act(current_obs[bank_name].astype(float), add_noise=False)
            actions[bank_name] = action  # this is where you use your RLAgents!
        # convert actions
        actions_dict = {}
        for name, action in actions.items():
            action_dict = {}
            action_dict[1], action_dict[2] = action[0], action[1]
            actions_dict[name] = action_dict
        new_obs, rewards, dones, infos = env.step(actions_dict)
        for bank_name, bank in env.allAgents_dict.items():
            if not bank.alive:
                continue
            my_new_obs = MA_obs_to_bank_obs(new_obs, bank)
            current_obs[bank_name] = my_new_obs
            RLagent_dict[bank_name].step(current_obs[bank_name], actions[bank_name], rewards[bank_name], my_new_obs, dones[bank_name])
        current_obs = new_obs
        num_default.append(infos['NUM_DEFAULTS'])
        play += 1
        if play == max_play:
            print(infos['AVERAGE_LIFESPAN'])
            average_lifespans.append(infos['AVERAGE_LIFESPAN'])

setup_matplotlib()
average_lifespans = np.array(average_lifespans).reshape((10, 100))
means_avg_lifespans = np.mean(average_lifespans, axis=1)
stds_avg_lifespans = np.std(average_lifespans, axis=1)
plot_custom_errorbar_plot(range(10), means_avg_lifespans, stds_avg_lifespans)
plt.savefig('lifespan.png')

    # plt.plot(num_default)
    # plt.ylabel('Number of defaults')
    # plt.show()
