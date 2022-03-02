## Learn@VCS Scraper

***A scraper for the learn@vcs website. The original website is dogwater and doesn't provide a comprehensive or consistent way of viewing assignments so here's a scraping application that attempts to do it for you.***

### Example Usage

```python
from datetime import datetime, timedelta
from learnvcs import Client, NavigationConfig, NoEntreeError

if __name__ == '__main__':
    courses = [433, 1446, 1154, 56, 1468]

    client = Client.login('Example.Username', 'ExamplePassword46')
    print(client.courses())

    for c in courses:
        try:
            print(client.homework(c))
        except NoEntreeError as e:
            print(e)
```
