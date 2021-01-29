# Bili_Comments
 经历了四次改版后的评论区爬取，希望能在单数据库下方便管理

# 环境要求
环境要求: Python 3  
```sh
    pip install -r requirements.txt
```
或者手动安装下列组件:  
- requests    用于与api通信  
- xmltodict   用于导出数据库为xml, 可选  
  
TODO: 将数据库筛选导出成表格  

# 使用方法

## 配置文件
打开config.csv, 直接编辑对应列的值即可。  
oid和type需要手动从Network栏中获取，格式如范例即可。  
尽量避免无意义的空格，不要更改表头，不要在表头中插入空格。  
```csv
replies_oid,type,alias
203766255,1,罗翔;提前安装防卫装置
``` 
alias是别名，在保存记录和导出记录的时候会用到。  

## 运行
在配置好环境的电脑上，打开终端，输入
```sh
    python3 ./main.py
```
每一轮爬取都会重载配置文件，所以config.csv中的编辑能够立即得到响应。  
  