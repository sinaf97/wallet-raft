# import redis
import uuid


class ACTIONS:
    GET_BALANCE = 0
    INCREASE_BALANCE = 1
    DECREASE_BALANCE = 2
    TRANSFER = 3
    NEW_WALLET = 4
    REMOVE_WALLET = 5
    REPLAY = 7


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

    def perform_action(self, action: ACTIONS, data: dict):
        if action == ACTIONS.GET_BALANCE:
            return self.wallets[data['wallet_id']]

        elif action == ACTIONS.INCREASE_BALANCE:
            self.wallets[data['wallet_id']] += data['amount']
            return self.wallets[data['wallet_id']]

        elif action == ACTIONS.DECREASE_BALANCE:
            if(self.wallets[data['wallet_id']] >= data['amount']):
                self.wallets[data['wallet_id']] -= data['amount']
                return self.wallets[data['wallet_id']]
            return None  # rejected

        elif action == ACTIONS.TRANSFER:
            if(self.wallets[data['origin_wallet_id']] >= data['amount']):
                self.wallets[data['origin_wallet_id']] -= data['amount']
                self.wallets[data['dest_wallet_id']] += data['amount']
                return self.wallets[data['origin_wallet_id']]
            return None  # rejected

        elif action == ACTIONS.NEW_WALLET:
            # generate a random id for wallet_id
            wallet_id = str(uuid.uuid1())
            self.wallets[wallet_id] = 0
            return {'wallet_id': wallet_id}

        elif action == ACTIONS.REMOVE_WALLET:
            return self.wallets.pop(data['wallet_id'])

        elif action == ACTIONS.REPLAY:
            return self.replay(data['result'], data)
        return None  # rejected

    def replay(self, result, data):
        result = data['result']
        data = data['data']
        action = data['action']

        if result['response'] == 'rejected':
            return None  # rejected

        if action == ACTIONS.GET_BALANCE:
            return self.wallets[data['wallet_id']]

        elif action == ACTIONS.INCREASE_BALANCE:
            self.wallets[data['wallet_id']] += data['amount']
            return self.wallets[data['wallet_id']]

        elif action == ACTIONS.DECREASE_BALANCE:
            if(self.wallets[data['wallet_id']] >= data['amount']):
                self.wallets[data['wallet_id']] -= data['amount']
                return self.wallets[data['wallet_id']]
            return None  # rejected

        elif action == ACTIONS.TRANSFER:
            if(self.wallets[data['origin_wallet_id']] >= data['amount']):
                self.wallets[data['origin_wallet_id']] -= data['amount']
                self.wallets[data['dest_wallet_id']] += data['amount']
                return self.wallets[data['origin_wallet_id']]
            return None  # rejected

        elif action == ACTIONS.NEW_WALLET:
            # generate a random id for wallet_id
            wallet_id = result['content']['wallet_id']
            self.wallets[wallet_id] = 0
            return {'wallet_id': wallet_id}

        elif action == ACTIONS.REMOVE_WALLET:
            return self.wallets.pop(data['wallet_id'])

        return None  # rejected
