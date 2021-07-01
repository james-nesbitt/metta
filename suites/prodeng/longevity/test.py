import threading
import time


class DomainOperations:
    def __init__(self):
        self.domain_ip = ""
        self.website_thumbnail = ""
        self.run()

    def resolve_domain(self):
        time.sleep(1)
        self.domain_ip = "foo"

    def generate_website_thumbnail(self):
        time.sleep(1)
        self.website_thumbnail = "bar"

    def run(self):
        t1 = threading.Thread(target=self.resolve_domain)
        t2 = threading.Thread(target=self.generate_website_thumbnail)
        t1.start()
        t2.start()
        print("Started")


if __name__ == "__main__":
    d = DomainOperations()
    time.sleep(3)
    print(d.domain_ip, d.website_thumbnail)
