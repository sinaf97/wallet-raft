# import redis
from client import CLIENT_ACTIONS
import uuid


class WalletManager:
    instance = None

    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = object.__new__(cls, *args, **kwargs)
        return cls.instance

    def __init__(self):
        self.wallets = {}

    # db = redis.Redis(
    #     host='hostname',
    #     port=port,
    #     password='password')

    def perform_action(self, action: CLIENT_ACTIONS, data: dict):
        print('heeeeeeeeeeeeeeeerrrrrrrrrrrrrrrrrrrrrreeeeeeeeeeeeeeeeeeeeeee',
              'performing the action', action)
        if action == CLIENT_ACTIONS.GET_BALANCE:
            return self.wallets[data['wallet_id']]

        elif action == CLIENT_ACTIONS.INCREASE_BALANCE:
            self.wallets[data['wallet_id']] += data['amount']
            return self.wallets[data['wallet_id']]

        elif action == CLIENT_ACTIONS.DECREASE_BALANCE:
            if(self.wallets[data['wallet_id']] >= data['amount']):
                self.wallets[data['wallet_id']] -= data['amount']
                return self.wallets[data['wallet_id']]
            return None  # rejected

        elif action == CLIENT_ACTIONS.TRANSFER:
            if(self.wallets[data['origin_wallet_id']] >= data['amount']):
                self.wallets[data['origin_wallet_id']] -= data['amount']
                self.wallets[data['dest_wallet_id']] += data['amount']
                return self.wallets[data['origin_wallet_id']]
            return None  # rejected

        elif action == CLIENT_ACTIONS.NEW_WALLET:
            # generate a random id for wallet_id
            wallet_id = str(uuid.uuid1())
            self.wallets[wallet_id] = 0
            return wallet_id

        elif action == CLIENT_ACTIONS.REMOVE_WALLET:
            return self.wallets.pop(data['wallet_id'])
        return None
