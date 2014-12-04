import sys
from collections import deque

current_price = {}
trades = {}

def read_file(filename):
	eof = False
	while True:
		line = filename.readline()
		if line == '' or line.rstrip() != '':
			break;
	if line == '': 
		eof = True
	else:
		line = line.rstrip().split(',')
	return eof, line

def generate_details(trade_info, price_info):
	side = trade_info[2]
	price = trade_info[3]
	bid = price_info[0]
	ask = price_info[1]
	liquidity = 'Err'
	if side == 'B':
		if price <= bid:
			liquidity = 'P'
		if price >= ask:
			liquidity = 'A'
	if side == 'S':
		if price <= bid:
			liquidity = 'A'
		if price >= ask:
			liquidity = 'P'
	return [trade_info,price_info,liquidity]

def price_bs(trade):
	if trade[2] == 'B':
		return float(trade[3])
	else:
		return -float(trade[3])

def print_output(open_trade, close_trade, ticker, quantity):
	no_error = True
	try:
		price_one = price_bs(open_trade[0]) + price_bs(close_trade[0])
	except:
		no_error = False
		price_one = 0

	pl = price_one * quantity
	print open_trade[0][0] + ',' + close_trade[0][0] + ',' + ticker + ',' + \
		str(quantity) + ',' +  ('%.2f' % (abs(pl)) if no_error else 'Err') + ',' + \
		open_trade[0][2] + ',' +  close_trade[0][2] + ',' + \
		open_trade[0][3] + ',' +  close_trade[0][3] + ',' + \
		open_trade[1][0] + ',' +  close_trade[1][0] + ',' + \
		open_trade[1][1] + ',' +  close_trade[1][1] + ',' + \
		open_trade[2] + ',' +  close_trade[2]

def generate_match(ticker, trade, quantity):
	close_trade = generate_details(trade,current_price[ticker])
	open_trade_list = trades[ticker][1]
	# this part we loop until all quantity of the trade has been fulfilled
	while (abs(quantity) > 0):
		#if there is matching open trade to fulfill the quantity
		if len(open_trade_list) > 0 :
			open_trade = trades[ticker][1].popleft()
			open_trade_quantity = return_quantity(open_trade[0])
			#if openinig trade is larger or equal than closing
			if abs(open_trade_quantity) >= abs(quantity):
				print_output(open_trade, close_trade, ticker, abs(quantity))
				trades[ticker][0] = trades[ticker][0] + quantity
				#if opening trade is larger, save the remainder quantity of the trade in front of the queue
				if abs(open_trade_quantity) - abs(quantity) > 0:
					open_trade[0][4] = str(int(open_trade[0][4]) + quantity)
					trades[ticker][1].appendleft(open_trade)
				quantity = 0
			#if opening trade is smaller than closing - calculate traded part of the opening trade
			else: 
				traded = abs(open_trade_quantity) * abs(quantity)/quantity
				print_output(open_trade, close_trade, ticker, abs(traded))
				quantity = quantity - traded
				trades[ticker][0] = trades[ticker][0] + traded
		#if there is no matching open trade to fulfill the quantity add the remainig quantity as opening trade
		elif (abs(quantity) > 0):
			trade[4] = str(abs(quantity))
			add_existing_trade(ticker, trade, quantity)
			trades[ticker][0] = trades[ticker][0] + quantity
			quantity = 0
	#if there is no trade for a ticker, remove the entry
	if trades[ticker][0] == 0:
		del trades[ticker]

def add_existing_trade(ticker, trade, quantity):
	trades[ticker][0] = trades[ticker][0] + quantity
	trade_details = generate_details(trade,current_price[ticker])
	trades[ticker][1].append(trade_details)

def add_new_trade(ticker, trade, quantity):
	trades[ticker] = [quantity, deque()]
	trade_details = generate_details(trade,current_price[ticker])
	trades[ticker][1].append(trade_details)

def process_quote(quote):
	current_price[quote[1]] = quote[2:]

def return_quantity(trade):
	quantity = int(trade[4])
	if trade[2] == 'S':
		quantity = -quantity
	return quantity

def process_trade(trade):
	ticker = trade[1]
	quantity = return_quantity(trade)
	if ticker in trades:
		if quantity * trades[ticker][0] > 0:
			add_existing_trade(ticker, trade, quantity)
		else :
			generate_match(ticker, trade, quantity)
	else:
		add_new_trade(ticker, trade, quantity)


if __name__ == '__main__':
	if len(sys.argv)<3:
		print "Program needs to be called as following:\npython vatic_code_test.py [quote_file] [trade_file]"
		sys.exit()

	try:
		quotes_f = open(sys.argv[1])		
	except:
		print "File %s does not exist. Expecting quotes file as first argument" % sys.argv[1]
		sys.exit()

	try:
		trades_f = open(sys.argv[2])	
	except:
		print "File %s does not exist. Expecting trades file as second argument" % sys.argv[2]
		sys.exit()

	quotes_is_eof = False
	trades_is_eof = False
	quotes_l = ''
	trades_l = ''
	quotes_f.readline()
	trades_f.readline()

	print 'OPEN_TIME,CLOSE_TIME,SYMBOL,QUANTITY,PNL,OPEN_SIDE,' + \
		'CLOSE_SIDE,OPEN_PRICE,CLOSE_PRICE,OPEN_BID,CLOSE_BID,' + \
		'OPEN_ASK,CLOSE_ASK,OPEN_LIQUIDITY,CLOSE_LIQUIDITY'

	while True:
		if not quotes_is_eof and quotes_l == '':
			quotes_is_eof, quotes_l = read_file(quotes_f)

		if not trades_is_eof and trades_l == '':			
			trades_is_eof, trades_l = read_file(trades_f)

		if not quotes_is_eof and not trades_is_eof:			
			if int(quotes_l[0]) <= int(trades_l[0]):
				process_quote(quotes_l)
				quotes_l = ''
			else:
				process_trade(trades_l)
				trades_l = ''
		elif not trades_is_eof:
			process_trade(trades_l)
			trades_l = ''

		if trades_is_eof:
			break

	quotes_f.close()
	trades_f.close()
	