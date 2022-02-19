## Learn@VCS Scraper

***A scraper for the learn@vcs website. The original website is dogwater and doesn't provide a comprehensive or consistent way of viewing assignments so here's a scraping application that attempts to do it for you.***

### Example Usage

```python
from learnvcs import Client, NoEntreeError

if __name__ == '__main__':
    courses = [433, 1446, 1154, 56, 1468]
    client = Client.login('example.username', 'ABadPassword45')

    for c in courses:
        try:
            print(client.homework(c))
        except NoEntreeError as e:
            print(str(e))
```
