{\rtf1\ansi\ansicpg1250\cocoartf2761
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww12720\viewh7800\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 \{\\rtf1\\ansi\\ansicpg1250\\cocoartf2761\
\\cocoatextscaling0\\cocoaplatform0\{\\fonttbl\\f0\\fswiss\\fcharset0 Helvetica;\}\
\{\\colortbl;\\red255\\green255\\blue255;\}\
\{\\*\\expandedcolortbl;;\}\
\\paperw11900\\paperh16840\\margl1440\\margr1440\\vieww11520\\viewh8400\\viewkind0\
\\pard\\tx720\\tx1440\\tx2160\\tx2880\\tx3600\\tx4320\\tx5040\\tx5760\\tx6480\\tx7200\\tx7920\\tx8640\\pardirnatural\\partightenfactor0\
\
\\f0\\fs24 \\cf0 function triggerButterflyEffect() \\\{\\\
    const container = document.getElementById('butterfly-container');\\\
    const butterflyCount = 12;\\\
\\\
    for (let i = 0; i < butterflyCount; i++) \\\{\\\
        const butterfly = document.createElement('div');\\\
        butterfly.className = 'butterfly';\\\
        butterfly.innerText = '\\uc0\\u55358 \\u56715 ';\\\
\\\
        // Start z do\\uc0\\u322 u ekranu z losowego miejsca\\\
        const startX = Math.random() * window.innerWidth;\\\
        butterfly.style.left = startX + 'px';\\\
        butterfly.style.bottom = '10px';\\\
\\\
        // Losowy kierunek lotu na boki\\\
        const dx = (Math.random() - 0.5) * 300 + 'px';\\\
        const dy = -(Math.random() * 300 + 200) + 'px';\\\
        \\\
        butterfly.style.setProperty('--dx', dx);\\\
        butterfly.style.setProperty('--dy', dy);\\\
\\\
        container.appendChild(butterfly);\\\
\\\
        // Usuni\\uc0\\u281 cie motyla po zako\\u324 czeniu animacji\\\
        setTimeout(() => \\\{\\\
            butterfly.remove();\\\
        \\\}, 2500);\\\
    \\\}\\\
\\\}\}}