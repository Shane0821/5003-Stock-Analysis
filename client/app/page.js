"use client"

import React, { useState, useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';

let now = new Date();
let freq = 60 / 1;
let size = freq * 3;
let seconds = 3 * 60 * 1000;
let value = Math.random() * 1000;

let data = [];
// for (var i = 0; i < 100; i++) {
//   data.push(randomData());
// }

function getSymbolSize(value) {
  if (value % 10 == 0) return 8;
  else if (value % 10 == 1) return 11;
  return 10;
}

function getSymbol(value) {
  if (value % 10 == 0) return 'triangle';
  else if (value % 10 == 1) return 'pin' // reverse triangle
  return 'none'
}

function getItemStyle(value) {
  if (value % 10 == 0) return {
    color: 'green'
  }
  return {
    color: 'red'
  }
}

function randomData() {
  now = new Date(+now + oneDay);
  value = value + Math.random() * 200 - 100;

  return {
    name: now.toString(),
    value: [
      [now.getFullYear(), now.getMonth(), now.getDate() + 1].join('/'),
      Math.round(value)
    ],
    symbol: getSymbol(Math.trunc(value)),
    itemStyle: getItemStyle(Math.trunc(value)),
    symbolSize: getSymbolSize(Math.trunc(value))
  };
}

function addNewStockData(_data) {
  console.log('stock data: ', _data)

  now = new Date(_data.timestamp);
  value = _data.regular_market_price;

  const newData = {
    name: now.toString(),
    value: [
      // [now.getHours(), now.getMinutes(), now.getSeconds()].join('/'),
      now.getTime(),
      value,
      [now.getFullYear(), now.getMonth(), now.getDate() + 1].join('/'),
    ],
    symbol: getSymbol(Math.trunc(value)),
    itemStyle: getItemStyle(Math.trunc(value)),
    symbolSize: getSymbolSize(Math.trunc(value))
  };

  if (data.length >= size) data.shift();
  else if (data.length > 0 && data[0].value[0] < newData.value[0] - seconds + 100) data.shift();
  data.push(newData)
}

export default function Home() {
  const [time, setTime] = useState(null);

  const [oneYearTargetEst, setOneYearTargetEst] = useState(null);
  const [askPrice, setAskPrice] = useState(null);
  const [askSize, setAskSize] = useState(null);
  const [averageVolume, setAverageVolume] = useState(null);
  const [beta, setBeta] = useState(null);
  const [bidPrice, setBidPrice] = useState(null);
  const [bidSize, setBidSize] = useState(null);
  const [eps, setEps] = useState(null);
  const [marketCap, setMarketCap] = useState(null);
  const [marketCapType, setMarketCapType] = useState(null);
  const [peRatio, setPeRatio] = useState(null);
  const [regularMarketChange, setRegularMarketChange] = useState(null);
  const [regularMarketChangePercent, setRegularMarketChangePercent] = useState(null);
  const [regularMarketOpen, setRegularMarketOpen] = useState(null);
  const [regularMarketPreviousClose, setRegularMarketPreviousClose] = useState(null);
  const [regularMarketPrice, setRegularMarketPrice] = useState(null);
  const [regularMarketVolume, setRegularMarketVolume] = useState(null);

  const stockSymbols = ['GOOGL', 'AAPL', 'AMZN', 'MSFT', 'TSLA'];
  // State to keep track of the selected option
  const [selectedSymbol, setSelectedSymbol] = useState(stockSymbols[0]);
  // Handler for when the select box value changes
  const handleSelectChange = (event) => {
    console.log(event.target.value)
    setSelectedSymbol(event.target.value);
  };

  const [option, setOption] = useState({
    // title: {
    //   text: 'Dynamic Data & Time Axis (GOOG)'
    // },
    tooltip: {
      trigger: 'axis',
      formatter: function (params) {
        params = params[0];
        var date = new Date(params.name);
        return (
          date.getDate() +
          '/' +
          (date.getMonth() + 1) +
          '/' +
          date.getFullYear() +
          ' : ' +
          ' ' +
          date.getHours() +
          ':' +
          date.getMinutes() +
          ':' +
          date.getSeconds() +
          ' : ' +
          params.value[1]
        );
      },
      axisPointer: {
        animation: false
      }
    },
    xAxis: {
      type: 'time',
      // min is current time
      min: new Date().getTime(),
      max: new Date().getTime() + seconds,
      splitLine: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
      min: 150,
      boundaryGap: [0, '100%'],
      splitLine: {
        show: false
      }
    },
    series: [
      {
        name: 'Fake Data',
        type: 'line',
        showSymbol: true,
        symbolSize: 9,
        markPoint: {
          data: data
        },
        data: data
      }
    ]
  })

  useEffect(() => {
    const ws = new WebSocket("ws://0.0.0.0:8766/");

    ws.onopen = () => {
      console.log('WebSocket connection established.');
    };

    ws.onmessage = function (event) {
      const newData = JSON.parse(event.data);

      if (newData.hasOwnProperty('regular_market_price')) {
        addNewStockData(newData);

        setOption(option => {
          const newOption = JSON.parse(JSON.stringify(option));
          newOption.series[0].markPoint.data = JSON.parse(JSON.stringify(data));
          newOption.series[0].data = JSON.parse(JSON.stringify(data));
          newOption.xAxis.min = data.length === 0 ? new Date().getTime() : data[0].value[0];
          newOption.xAxis.max = newOption.xAxis.min + seconds;
          return newOption;
        });

        setTime(new Date().toLocaleTimeString());
        setOneYearTargetEst(newData['1y_target_est']);
        setAskPrice(newData.ask_price);
        setAskSize(newData.ask_size);
        setAverageVolume(newData.average_volume);
        setBeta(newData.beta);
        setBidPrice(newData.bid);
        setBidSize(newData.bid_size);
        setEps(newData.eps);
        setMarketCap(newData.market_cap);
        setMarketCapType(newData.market_cap_type);
        setPeRatio(newData.pe_ratio);
        setRegularMarketChange(newData.regular_market_change);
        setRegularMarketChangePercent(newData.regular_market_change_percent);
        setRegularMarketOpen(newData.regular_market_open);
        setRegularMarketPreviousClose(newData.regular_market_previous_close);
        setRegularMarketPrice(newData.regular_market_price);
        setRegularMarketVolume(newData.regular_market_volume);
      } else if (newData.hasOwnProperty('rsi_signal')) {
        console.log('rsi_signal: ', newData);
      }
    };

    ws.onerror = (error) => {
      console.error(`WebSocket error: ${error}`);
    };

    ws.onclose = () => {
      console.log('WebSocket connection closed.');
    };

    return () => {
      console.log('Cleaning up WebSocket connection.');
      ws.close();
    };
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-between">
      <div className="flex flex-col items-center z-10 w-full justify-between font-mono text-sm">
        <div className="flex justify-between items-center p-4">
          <h1 className="text-lg font-semibold text-gray-800 mr-2">Dynamic Data & Time Axis</h1>
          <select
            value={selectedSymbol}
            onChange={handleSelectChange}
            className="border border-gray-300 rounded-md p-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-transparent"
          >
            {stockSymbols.map((symbol) => (
              <option key={symbol} value={symbol}>
                {symbol}
              </option>
            ))}
          </select>
        </div>
        <ReactECharts className="w-full" style={{ height: '80vh' }} option={option} />
        <div className="w-5/6 grid grid-cols-4 justify-items-start font-mono">
          <div>Regular Market Price: {regularMarketPrice}</div>
          <div>Regular Market Change: {regularMarketChange}</div>
          <div>Regular Market Change Percent: {regularMarketChangePercent}</div>
          <div>Regular Market Volume: {regularMarketVolume}</div>
          <div>Previous Close: {regularMarketPreviousClose}</div>
          <div>Open: {regularMarketOpen}</div>
          <div>One Year Target Est: {oneYearTargetEst}</div>
          <div>Ask Price: {askPrice}</div>
          <div>Ask Size: {askSize}</div>
          <div>Average Volume: {averageVolume}</div>
          <div>Beta: {beta}</div>
          <div>Bid Price: {bidPrice}</div>
          <div>Bid Size: {bidSize}</div>
          <div>EPS: {eps}</div>
          <div>Market Cap: {marketCap}</div>
          <div>Market Cap Type: {marketCapType}</div>
          <div>PE Ratio: {peRatio}</div>
        </div>
      </div>

      <div>
        <h1 className="text-center text-xs text-gray-400">
          {time ? `Last updated at ${time}` : ''}
        </h1>
      </div>
    </main>
  );
}
