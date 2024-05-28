"use client"

import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';

let now = new Date();
let freq = 60 / 1;
let size = freq * 3;
let seconds = 3 * 60 * 1000;
let value = Math.random() * 1000;

let data = [];
let signal = [];
// for (var i = 0; i < 100; i++) {
//   data.push(randomData());
// }

function getSymbolSize(v1, v2) {
  if (v1 == 1 && v2 == 1) return 9;
  else if (v1 == -1 && v2 == -1) return 12;
  return 10;
}

function getSymbol(v1, v2) {
  if (v1 == 1 && v2 == 1) return 'triangle'; // buy 1 sell -1
  else if (v1 == -1 && v2 == -1) return 'pin'
  return 'none'
}

function getItemStyle(v1, v2) {
  if (v1 == 1 && v2 == 1) return {
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
      " ",
      // [now.getFullYear(), now.getMonth(), now.getDate() + 1].join('/'),
    ],
    symbol: 'none',
    symbolSize: 10
  };

  if (data.length >= size) data.shift();
  else if (data.length > 0 && data[0].value[0] < newData.value[0] - seconds + 100) data.shift();
  data.push(newData)
}

function getSignalValue(signal) {
  const x = new Date(signal.timestamp).getTime()

  for (let i = 1; i < data.length; i++) {
    if (data[i].value[0] >= x && x >= data[i - 1].value[0]) {
      const x1 = data[i - 1].value[0]
      const x2 = data[i].value[0]
      const y1 = data[i - 1].value[1]
      const y2 = data[i].value[1]
      return y1 + (y2 - y1) * (x - x1) / (x2 - x1)
    }
  }

  return signal.moving_avg_price
}

function addNewSignal(_data) {
  console.log('signal: ', _data)

  now = new Date(_data.timestamp);
  value = getSignalValue(_data)

  const newData = {
    name: now.toString(),
    value: [
      // [now.getHours(), now.getMinutes(), now.getSeconds()].join('/'),
      now.getTime(),
      value,
      ` moving_avg_price: ${_data.moving_avg_price}`,
    ],
    symbol: getSymbol(_data.rsi_signal, _data.mac_signal),
    itemStyle: getItemStyle(_data.rsi_signal, _data.mac_signal),
    symbolSize: getSymbolSize(_data.rsi_signal, _data.mac_signal)
  };

  if (signal.length >= size) signal.shift();
  else if (signal.length > 0 && signal[0].value[0] < newData.value[0] - seconds + 100) signal.shift();
  signal.push(newData)
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
    console.log('symbol selected: ', event.target.value)
    setSelectedSymbol(event.target.value);
  };

  const strategy = ['RSI + MAC', 'OLS'];
  // State to keep track of the selected option
  const [selectedStrategy, setSelectedStrategy] = useState(strategy[0]);
  // Handler for when the select box value changes
  const handleSelectStrategyChange = (event) => {
    console.log('strategy selected: ', event.target.value)
    setSelectedStrategy(event.target.value);
  };

  const [option, setOption] = useState({
    // title: {
    //   text: 'Dynamic Data & Time Axis (GOOG)'
    // },
    lazyUpdate: false, // Update immediately
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
          params.value[1] +
          params.value[2]
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
        name: 'Data',
        type: 'line',
        showSymbol: true,
        z: 10,
        markPoint: {
          data: data
        },
        data: data,
        animation: false, // Disable animation for the series
      },
      {
        name: 'Signal',
        type: 'scatter',
        showSymbol: true,
        z: 20,
        markPoint: {
          data: data
        },
        data: data,
        animation: false, // Disable animation for the series
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
        addNewSignal(newData);

        setOption(option => {
          const newOption = JSON.parse(JSON.stringify(option));
          newOption.series[1].markPoint.data = JSON.parse(JSON.stringify(signal));
          newOption.series[1].data = JSON.parse(JSON.stringify(signal));
          return newOption;
        });
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

          <h1 className="ml-8 text-lg font-semibold text-gray-800 mr-2">Stock</h1>
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

          <h1 className="ml-8 text-lg font-semibold text-gray-800 mr-2">Strategy</h1>
          <select
            value={selectedStrategy}
            onChange={handleSelectStrategyChange}
            className="border border-gray-300 rounded-md p-2 text-gray-700 focus:outline-none focus:ring-2 focus:ring-transparent"
          >
            {strategy.map((symbol) => (
              <option key={symbol} value={symbol}>
                {symbol}
              </option>
            ))}
          </select>
        </div>
        <ReactECharts
          className="w-full"
          style={{ height: '80vh' }}
          option={option}
          opts={{
            notMerge: true,  // Prevent merging with the old option
            lazyUpdate: false, // Update immediately
          }}
        />
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
