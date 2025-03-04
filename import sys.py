import sys
import json
from functools import wraps
from typing import List, Dict, Optional
from dataclasses import dataclass
import requests
from pathlib import Path

# 装饰器用于计时函数执行
def time_it(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        import time
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = time.perf_counter() - start
        print(f"{func.__name__} 执行耗时: {duration:.4f}秒")
        return result
    return wrapper

# 数据类用于结构化数据
@dataclass
class Repository:
    name: str
    stars: int
    description: Optional[str]
    url: str

    def __str__(self):
        return f"{self.name} ({self.stars}★)"

# 上下文管理器处理文件操作
class JsonFileHandler:
    def __init__(self, filename: str):
        self.file = Path(filename)
        
    def __enter__(self):
        self.file.parent.mkdir(exist_ok=True, parents=True)
        return self.file
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            print(f"数据已保存至 {self.file}")

# 类型提示和生成器表达式
class GitHubAPI:
    def __init__(self, username: str):
        self.base_url = f"https://api.github.com/users/{username}/repos"
    
    @time_it
    def get_repos(self) -> List[Repository]:
        try:
            response = requests.get(self.base_url, timeout=5)
            response.raise_for_status()
            return self._parse_response(response.json())
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {str(e)}")
            sys.exit(1)
    
    def _parse_response(self, data: List[Dict]) -> List[Repository]:
        return [
            Repository(
                name=repo["name"],
                stars=repo["stargazers_count"],
                description=repo["description"],
                url=repo["html_url"]
            ) for repo in data if not repo["fork"]
        ]

def main(username: str):
    # 使用pathlib处理路径
    output_file = Path("output") / "repos.json"
    
    api = GitHubAPI(username)
    repos = api.get_repos()
    
    # 多重排序：按星标降序，名称升序
    sorted_repos = sorted(repos, 
                         key=lambda x: (-x.stars, x.name))
    
    # 使用walrus运算符 (Python 3.8+)
    if (top_repo := next(iter(sorted_repos), None)):
        print(f"\n⭐ 最受欢迎的仓库: {top_repo}")
    
    # 使用f-string格式化输出
    print(f"\n🏆 共找到 {len(repos)} 个非fork仓库")
    
    # 生成器表达式过滤数据
    popular = sum(1 for r in repos if r.stars > 100)
    print(f"🔥 超过100星的仓库: {popular}个")
    
    # 上下文管理器处理文件操作
    with JsonFileHandler(output_file) as f:
        f.write_text(json.dumps(
            [repo.__dict__ for repo in sorted_repos],
            indent=2, ensure_ascii=False
        ))

if __name__ == "__main__":
    try:
        username = sys.argv[1]
    except IndexError:
        username = input("请输入GitHub用户名: ")
    
    main(username)