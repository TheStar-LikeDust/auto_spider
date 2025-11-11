# auto_spider

## 智能爬虫

目标
> 能够接收自然语言命令，去自动解析社交或新闻网站，生成对应的爬取策略并判断是否获取到了目标数据

最终
> 能够代替人类去访问各类网站


### 组件

- 爬虫模块 selenium
- 任务分发器
- 基于LLM的策略链


## 快速开始

```python
from auto_spider.components import RequestSpider

spider = RequestSpider()
spider.attach()

response = spider.do_url('https://example.com', retry=3)
html = response.text

spider.detach()
```

## 爬虫组件库

提供基本的爬虫组件库，可以让大模型辅助构建基本的爬虫程序

### actions

actions作为爬虫具体逻辑，一个action对应一个简单的操作，比如提交表单，点击按钮，跳转到某个页面等

- 可以被action loader找到，只要通过继承的方式实现了Action基类存放在不同模块中也可以被找到并全局加载  
    - 可以通过装饰器的方式激活action
- 可以通过类似管道的方式组合多个action并且传递数据，通过额外的参数注入管道数据的数据
- 
