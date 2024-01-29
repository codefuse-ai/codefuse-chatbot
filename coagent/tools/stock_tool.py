
import json
import os
import re
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import requests
import numpy as np
from loguru import logger

from .base_tool import BaseToolModel
from coagent.utils.common_utils import read_json_file

from .tool_datas.stock_data import stock_infos
# cur_dir = os.path.dirname(os.path.abspath(__file__))
# stock_infos = read_json_file(os.path.join(cur_dir, "tool_datas/stock.json"))
stock_dict = {i["mc"]: i["jys"]+i["dm"] for i in stock_infos}


class StockName(BaseToolModel):
    """
    Tips
    """
    name: str = "StockName"
    description: str = "通过股票名称查询股票代码"

    class ToolInputArgs(BaseModel):
        """Input for StockName"""
        stock_name: int = Field(..., description="股票名称")

    class ToolOutputArgs(BaseModel):
        """Output for StockName"""
        stock_code: str = Field(..., description="股票代码")
    
    @staticmethod
    def run(stock_name: str):
        return stock_dict.get(stock_name, "no stock_code")
    


class StockInfo(BaseToolModel):
    """
    用于查询股票市场数据的StockInfo工具。
    """

    name: str = "StockInfo"
    description: str = "根据提供的股票代码、日期范围和数据频率提供股票市场数据。"

    class ToolInputArgs(BaseModel):
        """StockInfo的输入参数。"""
        code: str = Field(..., description="要查询的股票代码，格式为'marketcode'")
        end_date: Optional[str] = Field(default="", description="数据查询的结束日期。留空则为当前日期。如果没有提供结束日期，就留空")
        count: int = Field(default=10, description="返回数据点的数量。")
        frequency: str = Field(default='1d', description="数据点的频率，例如，'1d'表示每日，'1w'表示每周，'1M'表示每月，'1m'表示每分钟等。")

    class ToolOutputArgs(BaseModel):
        """StockInfo的输出参数。"""
        data: dict = Field(default=None, description="查询到的股票市场数据。")

    @staticmethod
    def run(code: str, count: int, frequency: str, end_date: Optional[str]="") -> "ToolOutputArgs":
        """执行股票数据查询工具。"""
        # 该方法封装了调用底层股票数据API的逻辑，并将结果格式化为pandas DataFrame。
        try:
            df = get_price(code, end_date=end_date, count=count, frequency=frequency)
            # 将DataFrame转换为输出的字典格式
            data = df.reset_index().to_dict(orient='list')  # 将dataframe转换为字典列表
            return StockInfo.ToolOutputArgs(data=data)
        except Exception as e:
            logger.exception("获取股票数据时发生错误。")
            return e

#-*- coding:utf-8 -*-    --------------Ashare 股票行情数据双核心版( https://github.com/mpquant/Ashare ) 

import json,requests,datetime
import pandas as pd  #

#腾讯日线

def get_price_day_tx(code, end_date='', count=10, frequency='1d'):     #日线获取  

    unit='week' if frequency in '1w' else 'month' if frequency in '1M' else 'day'     #判断日线，周线，月线

    if end_date:  end_date=end_date.strftime('%Y-%m-%d') if isinstance(end_date,datetime.date) else end_date.split(' ')[0]

    end_date='' if end_date==datetime.datetime.now().strftime('%Y-%m-%d') else end_date   #如果日期今天就变成空    

    URL=f'http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={code},{unit},,{end_date},{count},qfq'     

    st= json.loads(requests.get(URL).content);    ms='qfq'+unit;      stk=st['data'][code]   

    buf=stk[ms] if ms in stk else stk[unit]       #指数返回不是qfqday,是day

    df=pd.DataFrame(buf,columns=['time','open','close','high','low','volume'],dtype='float')     

    df.time=pd.to_datetime(df.time);    df.set_index(['time'], inplace=True);   df.index.name=''          #处理索引 

    return df


#腾讯分钟线

def get_price_min_tx(code, end_date=None, count=10, frequency='1d'):    #分钟线获取 

    ts=int(frequency[:-1]) if frequency[:-1].isdigit() else 1           #解析K线周期数

    if end_date: end_date=end_date.strftime('%Y-%m-%d') if isinstance(end_date,datetime.date) else end_date.split(' ')[0]        

    URL=f'http://ifzq.gtimg.cn/appstock/app/kline/mkline?param={code},m{ts},,{count}' 

    st= json.loads(requests.get(URL).content);       buf=st[ 'data'][code]['m'+str(ts)] 

    df=pd.DataFrame(buf,columns=['time','open','close','high','low','volume','n1','n2'])   

    df=df[['time','open','close','high','low','volume']]    

    df[['open','close','high','low','volume']]=df[['open','close','high','low','volume']].astype('float')

    df.time=pd.to_datetime(df.time);   df.set_index(['time'], inplace=True);   df.index.name=''          #处理索引     

    df['close'][-1]=float(st['data'][code]['qt'][code][3])                #最新基金数据是3位的

    return df


#sina新浪全周期获取函数，分钟线 5m,15m,30m,60m  日线1d=240m   周线1w=1200m  1月=7200m

def get_price_sina(code, end_date='', count=10, frequency='60m'):    #新浪全周期获取函数    

    frequency=frequency.replace('1d','240m').replace('1w','1200m').replace('1M','7200m');   mcount=count

    ts=int(frequency[:-1]) if frequency[:-1].isdigit() else 1       #解析K线周期数

    if (end_date!='') & (frequency in ['240m','1200m','7200m']): 

        end_date=pd.to_datetime(end_date) if not isinstance(end_date,datetime.date) else end_date    #转换成datetime
        unit=4 if frequency=='1200m' else 29 if frequency=='7200m' else 1    #4,29多几个数据不影响速度

        count=count+(datetime.datetime.now()-end_date).days//unit            #结束时间到今天有多少天自然日(肯定 >交易日)        

        #print(code,end_date,count)    

    URL=f'http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={code}&scale={ts}&ma=5&datalen={count}' 

    dstr= json.loads(requests.get(URL).content);       

    #df=pd.DataFrame(dstr,columns=['day','open','high','low','close','volume'],dtype='float') 

    df= pd.DataFrame(dstr,columns=['day','open','high','low','close','volume'])

    df['open'] = df['open'].astype(float); df['high'] = df['high'].astype(float);                          #转换数据类型
    df['low'] = df['low'].astype(float);   df['close'] = df['close'].astype(float);  df['volume'] = df['volume'].astype(float)    

    df.day=pd.to_datetime(df.day);    

    df.set_index(['day'], inplace=True);     

    df.index.name=''            #处理索引                 

    if (end_date!='') & (frequency in ['240m','1200m','7200m']): 
        return df[df.index<=end_date][-mcount:]   #日线带结束时间先返回              

    return df


def get_price(code, end_date='',count=10, frequency='1d', fields=[]):        #对外暴露只有唯一函数，这样对用户才是最友好的  

    xcode= code.replace('.XSHG','').replace('.XSHE','')                      #证券代码编码兼容处理 
    xcode='sh'+xcode if ('XSHG' in code)  else  'sz'+xcode  if ('XSHE' in code)  else code     

    if  frequency in ['1d','1w','1M']:   #1d日线  1w周线  1M月线
        try:    
            return get_price_sina( xcode, end_date=end_date,count=count,frequency=frequency)   #主力
        except: 
            return get_price_day_tx(xcode,end_date=end_date,count=count,frequency=frequency)   #备用                    

    if  frequency in ['1m','5m','15m','30m','60m']:  #分钟线 ,1m只有腾讯接口  5分钟5m   60分钟60m
        if frequency in '1m': 
            return get_price_min_tx(xcode,end_date=end_date,count=count,frequency=frequency)
        try:
            return get_price_sina(xcode,end_date=end_date,count=count,frequency=frequency)   #主力   
        except: 
            return get_price_min_tx(xcode,end_date=end_date,count=count,frequency=frequency)   #备用


if __name__ == "__main__":
    tool = StockInfo()
    output = tool.run(code='sh600519', end_date='', count=10, frequency='15m')
    print(output.json(indent=2))