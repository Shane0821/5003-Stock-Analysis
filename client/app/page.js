"use client"

import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';

let now = new Date();
let oneDay = 24 * 3600 * 1000;
let value = Math.random() * 1000;

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
  value = value + Math.random() * 21 - 10;

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

let data = [];
for (var i = 0; i < 180; i++) {
  data.push(randomData());
}

export default function Home() {
  const [time, setTime] = useState(null);

  // const ws = new WebSocket("ws://localhost:8766/");
  const [option, setOption] = useState({
    title: {
      text: 'Dynamic Data & Time Axis'
    },
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
          params.value[1]
        );
      },
      axisPointer: {
        animation: false
      }
    },
    xAxis: {
      type: 'time',
      splitLine: {
        show: false
      }
    },
    yAxis: {
      type: 'value',
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
    const intervalId = setInterval(function () {
      data.shift()
      data.push(randomData())

      console.log("haaha")

      setOption(option => {
        const newOption = JSON.parse(JSON.stringify(option));
        newOption.series[0].markPoint.data = JSON.parse(JSON.stringify(data))
        newOption.series[0].data = JSON.parse(JSON.stringify(data))
        return newOption;
      });

      setTime(new Date().toLocaleTimeString());
    }, 1000);

    return () => {
      // ws.close();
      clearInterval(intervalId);
    }
  })

  return (
    <main className="flex min-h-screen flex-col items-center justify-between">
      <div className="z-10 w-full items-center justify-between font-mono text-sm">
        <ReactECharts className="w-full" style={{ height: '85vh' }} option={option} />
        <div className="grid justify-items-center font-mono">
          {data[data.length - 1] ? data[data.length - 1].name : ''}
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
