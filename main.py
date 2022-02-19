import logging
from __init__ import Client, NoEntreeError

if __name__ == '__main__':
    courses = [433, 1446, 1154, 56, 1468]

    with open('credentials', 'r') as f:
        username, password, *_ = f.read().split('\n')
        client = Client.login(username, password)
        logging.debug(client.courses())
        for c in courses:
            try:
                print(client.homework(c))
            except NoEntreeError as e:
                logging.error(str(e))
