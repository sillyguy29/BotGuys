bot.o: bot.c
	gcc bot.c -o bot.o

clean:
	rm -f bot.o