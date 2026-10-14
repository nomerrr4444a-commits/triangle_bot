import threading
import time
import ccxt
from flask import Flask
import telebot

app = Flask(__name__)


@app.route("/")
def home():
  return "🤖 Bot is running!"


# Встав сюди свій токен від BotFather:
TOKEN = "8635304491:AAEBvuKCl5Prbryev195nFcqA3_uCIzYsnc"
bot = telebot.TeleBot(TOKEN)

exchange = ccxt.binance({"enableRateLimit": True})

virtual_balance = 100.0
total_profit = 0.0
total_loss = 0.0
user_chat_id = None


@bot.message_handler(commands=["start"])
def send_welcome(message):
  global user_chat_id
  user_chat_id = message.chat.id
  bot.reply_to(
      message,
      "🤖 Симулятор трикутників активовано!\nЯ рахую результати з урахуванням"
      " комісій на кожному кроці з банку $100.",
  )
  print(f"✅ Збережено Chat ID користувача: {user_chat_id}")


def simulate_triangle_trading():
  global virtual_balance, total_profit, total_loss

  print("⏳ Чекаю команду /start у Telegram...")
  while user_chat_id is None:
    time.sleep(1)

  bot.send_message(
      user_chat_id,
      "🚀 Симулятор запущено! Початковий банк: $100.00 (комісія 0.1% на кожній"
      " операції)",
  )

  while True:
    try:
      tickers = exchange.fetch_tickers(["BTC/USDT", "ETH/BTC", "ETH/USDT"])
      price_btc_usdt = tickers["BTC/USDT"]["ask"]
      price_eth_btc = tickers["ETH/BTC"]["ask"]
      price_eth_usdt = tickers["ETH/USDT"]["bid"]

      # Початковий капітал
      start_amount = 100.0
      fee_rate = 0.001  # 0.1% комісія біржі за кожну угоду

      # Крок 1: Купуємо BTC за USDT (мінус комісія)
      btc_amount = (start_amount / price_btc_usdt) * (1 - fee_rate)

      # Крок 2: Купуємо ETH за BTC (мінус комісія)
      eth_amount = (btc_amount / price_eth_btc) * (1 - fee_rate)

      # Крок 3: Продаємо ETH назад за USDT (мінус комісія)
      end_amount = (eth_amount * price_eth_usdt) * (1 - fee_rate)

      # Чистий результат угоди
      profit_loss = end_amount - start_amount

      if profit_loss > 0:
        trade_type = "🟢 ТЕЙК (ПРИБУТОК)"
        total_profit += profit_loss
      else:
        trade_type = "🔴 МІНУС (ЗБИТОК)"
        total_loss += abs(profit_loss)

      virtual_balance += profit_loss

      msg = (
          f"🔄 <b>Угоду закрито!</b>\n\n"
          f"📊 Статус: {trade_type}\n"
          f"💵 Результат угоди: <code>{round(profit_loss, 4)} $</code>\n"
          f"💰 Загальний баланс: <code>{round(virtual_balance, 2)} $</code>\n"
          f"📈 Загальний прибуток: +{round(total_profit, 2)} $\n"
          f"📉 Загальний мінус: -{round(total_loss, 2)} $\n"
      )
      bot.send_message(user_chat_id, msg, parse_mode="HTML")

      # Перевірка кожну хвилину
      time.sleep(60)

    except Exception as e:
      print(f"Помилка: {e}")
      time.sleep(10)


def run_telegram_bot():
  bot.infinity_polling()


if __name__ == "__main__":
  t1 = threading.Thread(target=simulate_triangle_trading, daemon=True)
  t1.start()
  t2 = threading.Thread(target=run_telegram_bot, daemon=True)
  t2.start()
  app.run(host="0.0.0.0", port=10000)
