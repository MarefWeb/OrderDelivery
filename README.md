# Telegram bot
Bot for receiving and processing orders in Telegram.
### How does the bot work?
1. The customer answers the bot's questions.

2. After the customer has answered all the questions the bot sends the processed version of the order to the telegram channel with administrators and asks to wait for the customer to answer.  

3. The channel receives the order and under it two buttons "accept" and "reject".  

4. A). When clicking on the "accept" button, all the order data is entered into the google table and the client receives a message that the order has been accepted.  
B). When clicking on the "reject" button, the order is deleted from the chat and the client receives a message about rejection.  
