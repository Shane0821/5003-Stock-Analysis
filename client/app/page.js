"use client"
import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';

let now = new Date(1997, 9, 3);
let oneDay = 24 * 3600 * 1000;
let value = Math.random() * 1000;
function randomData() {
  now = new Date(+now + oneDay);
  value = value + Math.random() * 21 - 10;
  return {
    name: now.toString(),
    value: [
      [now.getFullYear(), now.getMonth() + 1, now.getDate()].join('/'),
      Math.round(value)
    ]
  };
}

let data = [];
for (var i = 0; i < 1000; i++) {
  data.push(randomData());
}

export default function Home() {
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
        showSymbol: false,
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
        newOption.series[0].data = JSON.parse(JSON.stringify(data))
        return newOption;
      });
    }, 1000);

    return () => {
      // ws.close();
      clearInterval(intervalId);
    }
  })

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <ReactECharts className="w-full h-full" option={option} />
      </div>
    </main>
  );
}
