import threading
import time
import ccxt
from flask import Flask
import telebot

# 1. Веб-сервер для Render (обязательно, чтобы хостинг не выдавал ошибку)
app = Flask(__name__)


@app.route("/")
def home():
  return "🤖 Crypto Arb Bot & Triangle Simulator is running successfully!"


# 2. Настройка Telegram бота
TOKEN = "8635304491:AAEBvuKCl5Prbryev195nFcqA3_uCIzYsnc"
bot = telebot.TeleBot(TOKEN)

# Подключение к бирже для получения реальных цен
exchange = ccxt.binance({"enableRateLimit": True})

# Виртуальный капитал и статистика
virtual_balance = 100.0
total_profit = 0.0
total_loss = 0.0
user_chat_id = None  # Сюда автоматически запишется твой ID


@bot.message_handler(commands=["start"])
def send_welcome(message):
  global user_chat_id
  user_chat_id = message.chat.id
  bot.reply_to(
      message,
      "🤖 Симулятор трикутників активовано!\nЯ стежу за ринком і надсилатиму"
      " звіти про кожну угоду сюди.",
  )
  print(f"✅ Збережено Chat ID користувача: {user_chat_id}")


def simulate_triangle_trading():
  global virtual_balance, total_profit, total_loss

  print("⏳ Чекаю команду /start у Telegram від тебе...")
  while user_chat_id is None:
    time.sleep(1)

  bot.send_message(
      user_chat_id, "🚀 Симулятор угод запущено! Початковий банк: $100.00"
  )

  while True:
    try:
      # Загружаем реальные цены для треугольника
      tickers = exchange.fetch_tickers(["BTC/USDT", "ETH/BTC", "ETH/USDT"])

      price_btc_usdt = tickers["BTC/USDT"]["ask"]
      price_eth_btc = tickers["ETH/BTC"]["ask"]
      price_eth_usdt = tickers["ETH/USDT"]["bid"]

      # Расчет результата круга на $100
      start_amount = 100.0
      step1 = start_amount / price_btc_usdt  # Купили BTC
      step2 = step1 / price_eth_btc  # Купили ETH за BTC
      end_amount = step2 * price_eth_usdt  # Продали ETH за USDT

      # Комиссия биржи (~0.3% за 3 шага)
      fee = end_amount * 0.003
      net_result = end_amount - fee
      profit_loss = net_result - start_amount

      if profit_loss > 0:
        trade_type = "🟢 ТЕЙК (ПРИБУТОК)"
        total_profit += profit_loss
      else:
        trade_type = "🔴 МІНУС (ЗБИТОК)"
        total_loss += abs(profit_loss)

      virtual_balance += profit_loss

      # Формируем отчет в Telegram
      msg = (
          f"🔄 <b>Угоду закрито!</b>\n\n"
          f"📊 Статус: {trade_type}\n"
          f"💵 Результат угоди: <code>{round(profit_loss, 2)} $</code>\n"
          f"💰 Загальний баланс: <code>{round(virtual_balance, 2)} $</code>\n"
          f"📈 Загальний прибуток: +{round(total_profit, 2)} $\n"
          f"📉 Загальний мінус: -{round(total_loss, 2)} $\n"
      )

      bot.send_message(user_chat_id, msg, parse_mode="HTML")

      # Пауза между симуляциями угод (например, 60 секунд)
      time.sleep(60)

    except Exception as e:
      print(f"Помилка в симуляторі: {e}")
      time.sleep(10)


def run_telegram_bot():
  bot.infinity_polling()


if __name__ == "__main__":
  # Запускаем симулятор в отдельном потоке
  t1 = threading.Thread(target=simulate_triangle_trading, daemon=True)
  t1.start()

  # Запускаем Telegram-бота в отдельном потоке
  t2 = threading.Thread(target=run_telegram_bot, daemon=True)
  t2.start()

  # Запускаем Flask-сервер (нужно для Render)
  app.run(host="0.0.0.0", port=10000)
