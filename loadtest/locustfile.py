from random import choice
from uuid import uuid4
from locust import HttpUser, task, between

class ShortenerUser(HttpUser):
    wait_time = between(1, 3)

    codes : list[str]

    def on_start(self):
        """每个用户启动时，先创建几条短链备用"""
        self.codes = []
        for _ in range(3):
            resp = self.client.post(
                "/short",
                json={"url": f"https://example.com/{uuid4()}", "expire_in": 9600}
            )
            if resp.status_code in (200, 201):
                try:
                    self.codes.append(resp.json()["code"])
                except (ValueError, KeyError):
                    pass

        if not self.codes:
            raise RuntimeError("Fail to create any short code during start.")

    @task(10)
    def redirect(self):
        """模拟用户访问短链（读操作，命中缓存）"""
        if not self.codes:
            return
        code = choice(self.codes)
        self.client.get(f"/{code}", name="/[code]", allow_redirects=False)

    @task(1)
    def create_shortlink(self):
        """模拟新建短链"""
        self.client.post(
            "/short",
            json={"url": f"https://example.com/{uuid4()}", "expire_in": 9600},
            name="/short"
        )
