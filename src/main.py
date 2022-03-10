from datetime import datetime
from learnvcs import Client, NavigationConfig, NoEntreeError

if __name__ == '__main__':
    courses = [433, 1446, 1154, 56, 1468]
    # courses = [56]

    with open('credentials', 'r') as f:
        username, password, *_ = f.read().split('\n')
        client = Client.login(username, password)
        print(client.courses())

        for c in courses:
            try:
                print(client.homework(c, NavigationConfig(datetime(2022, 3, 4))))
            except NoEntreeError as e:
                print(e)
