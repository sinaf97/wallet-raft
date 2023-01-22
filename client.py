import json
import requests


class CLIENT_ACTIONS:
    GET_BALANCE = 0
    INCREASE_BALANCE = 1
    DECREASE_BALANCE = 2
    TRANSFER = 3
    NEW_WALLET = 4
    REMOVE_WALLET = 5


class Client:
    def run(self):
        while True:
            print("Welcome...")
            print("1. Balance")
            print("2. Increase Balance")
            print("3. Decrease Balance")
            print("4. transfer")
            print("5. New Wallet")
            print("6. Remove Wallet")
            print("7. Exit")

            self.handle_choice(int(input("Please choose: ")))

    def handle_choice(self, choice):
        if choice == 7:
            exit(0)
        elif choice == 1:
            self.get_balance()
        elif choice == 2:
            self.increase_balance()
        elif choice == 3:
            self.decrease_balance()
        elif choice == 4:
            self.transfer()
        elif choice == 5:
            self.new_wallet()
        elif choice == 6:
            self.remove_wallet()
        else:
            print("Not a valid option...")

    def get_balance(self):
        wallet_id = input("What is your wallet ID: ")
        response = self.send_request({
            "action": CLIENT_ACTIONS.GET_BALANCE,
            "wallet_id": wallet_id
        })
        # print result
        print(json.loads(response.content)["body"])

    def increase_balance(self):
        wallet_id = input("What is your wallet ID: ")
        amount = input("How much do you want to deposit: ")
        response = self.send_request({
            "action": CLIENT_ACTIONS.INCREASE_BALANCE,
            "wallet_id": wallet_id,
            "amount": float(amount)
        }, "/add")
        # print result
        print(json.loads(response.content)["body"])

    def decrease_balance(self):
        wallet_id = input("What is your wallet ID: ")
        amount = input("How much do you want to check out: ")
        response = self.send_request({
            "action": CLIENT_ACTIONS.DECREASE_BALANCE,
            "wallet_id": wallet_id,
            "amount": float(amount)
        })
        # print result
        print(json.loads(response.content)["body"])

    def transfer(self):
        origin_wallet_id = input("What is the origin wallet ID: ")
        dest_wallet_id = input("What is the destination wallet ID: ")
        amount = input("How much do you want to transfer: ")
        response = self.send_request({
            "action": CLIENT_ACTIONS.TRANSFER,
            "origin_wallet_id": origin_wallet_id,
            "dest_wallet_id": dest_wallet_id,
            "amount": float(amount)
        })
        # print result
        print(json.loads(response.content)["body"])

    def new_wallet(self):
        response = self.send_request({
            "action": CLIENT_ACTIONS.NEW_WALLET
        })
        # print result
        print(json.loads(response.content)["body"])

        # returns wallet id

    def remove_wallet(self):
        wallet_id = input("What is the wallet ID that you want to remove: ")
        response = self.send_request({
            "action": CLIENT_ACTIONS.REMOVE_WALLET,
            "wallet_id": wallet_id,
        })
        # print result
        print(json.loads(response.content)["body"])

    def send_request(self, payload, path="/add"):
        with open("leader", "r") as f:
            port = f.read()

        url = f"http://127.0.0.1:{port}{path}"
        return requests.post(url, json=payload)


if __name__ == '__main__':
    cl = Client()
    cl.run()
