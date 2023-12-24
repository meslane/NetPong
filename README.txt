~== GAMEPLAY ==~
    160 (x) by 90 (y) playfield
    
~== CURRENT BUGS ==~
    -Hits on the left paddle upper side occasionally deflect upwards and back instead of upwards and forward [FIXED]
	-Can reliabily reproduce
	-Seems to be caused by multiple hits registering in a short period
	-Added hit timeout to fix

    -Netcode is extremely shitty [FIXED]
        -Users frequenty desync because of all the separate threads
        -Gets slower to respond over time
        -Should move all netcode into one thread

        -Improved on server side by using select module
        -Need to fix client
        -Problem is that server is so much faster, it's overwhelming the client with packets
        -Keep track of last sent packet and have a timer of some sort

    -Server has a memory leak after implementing non blocking sockets [FIXED]
        -Seems to happen after closing the first connection
        -Fixed by adding exception handling