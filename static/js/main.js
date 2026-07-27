{\rtf1\ansi\ansicpg1250\cocoartf2761
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww12720\viewh7800\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 document.addEventListener('DOMContentLoaded', () => \{\
    // Logowanie\
    const loginForm = document.getElementById('login-form');\
    if (loginForm) \{\
        loginForm.addEventListener('submit', async (e) => \{\
            e.preventDefault();\
            const username = document.getElementById('username').value;\
            const formData = new FormData();\
            formData.append('username', username);\
\
            const res = await fetch('/register', \{ method: 'POST', body: formData \});\
            const data = await res.json();\
            if (data.success) \{\
                window.location.reload();\
            \}\
        \});\
    \}\
\
    // Formularz Przelewu\
    const transferForm = document.getElementById('transfer-form');\
    if (transferForm) \{\
        transferForm.addEventListener('submit', async (e) => \{\
            e.preventDefault();\
            const receiver_id = document.getElementById('receiver').value;\
            const amount = document.getElementById('amount').value;\
\
            const res = await fetch('/transfer', \{\
                method: 'POST',\
                headers: \{ 'Content-Type': 'application/json' \},\
                body: JSON.stringify(\{ receiver_id, amount \})\
            \});\
\
            const data = await res.json();\
            if (data.success) \{\
                triggerButterflyEffect();\
                alert(data.message);\
                setTimeout(() => window.location.reload(), 1500);\
            \} else \{\
                alert(data.message);\
            \}\
        \});\
    \}\
\});\
\
// Funkcje Panelu Admina\
async function adjustCoins(userId, amount) \{\
    const res = await fetch('/admin/adjust_balance', \{\
        method: 'POST',\
        headers: \{ 'Content-Type': 'application/json' \},\
        body: JSON.stringify(\{ user_id: userId, amount: amount \})\
    \});\
    const data = await res.json();\
    if (data.success) window.location.reload();\
\}\
\
async function kickUser(userId, username) \{\
    if (confirm(`Na pewno chcesz usun\uc0\u261 \u263  gracza $\{username\}?`)) \{\
        const res = await fetch('/admin/kick_user', \{\
            method: 'POST',\
            headers: \{ 'Content-Type': 'application/json' \},\
            body: JSON.stringify(\{ user_id: userId \})\
        \});\
        const data = await res.json();\
        if (data.success) window.location.reload();\
    \}\
\}}