"""
Flask Web App for Blackjack AI
Modern web interface to watch the AI play and interact with the game
"""

from flask import Flask, render_template, jsonify, request
import json
from blackjackai import BlackjackGame, Card, Hand, BasicStrategy

app = Flask(__name__)

# Global game instance
game = None
gameHistory = []


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/new-game', methods=['POST'])
def newGame():
    """Start a new game with specified settings"""
    global game, gameHistory

    data = request.json

    game = BlackjackGame(
        startingBankroll=float(data.get('bankroll', 1000)),
        baseBet=float(data.get('baseBet', 10)),
        useCardCounting=data.get('useCardCounting', True),
        useWonging=data.get('useWonging', True),
        wongingThreshold=float(data.get('wongingThreshold', -1.0)),
        penetration=float(data.get('penetration', 0.75))
    )

    gameHistory = []

    return jsonify({
        'success': True,
        'bankroll': game.bankroll,
        'baseBet': game.baseBet,
        'useCardCounting': game.useCardCounting,
        'useWonging': game.useWonging
    })


@app.route('/api/play-hand', methods=['POST'])
def playHand():
    """Play one hand and return the results"""
    global game, gameHistory

    if game is None:
        return jsonify({'error': 'No game started'}), 400

    # Capture hand details
    handData = {
        'handNumber': game.handsPlayed + game.handsSatOut + 1,
        'bankrollBefore': game.bankroll,
        'runningCount': game.counter.runningCount,
        'trueCount': game.counter.getTrueCount(game.deck.decksRemaining()),
        'decksRemaining': game.deck.decksRemaining(),
    }

    # Check if we need to reshuffle
    needsReshuffle = game.deck.needsReshuffle(game.reshufflePoint)
    if needsReshuffle:
        game.deck.reset()
        game.counter.reset()
        handData['reshuffle'] = True

    # Check if sitting out
    trueCount = game.counter.getTrueCount(game.deck.decksRemaining())
    if game.useWonging and trueCount < game.wongingThreshold:
        # Sitting out
        game.handsSatOut += 1

        # Burn some cards to maintain count
        burnedCards = []
        for _ in range(4):
            if len(game.deck.cards) > 0:
                card = game.deck.dealCard()
                game.counter.countCard(card)
                burnedCards.append({'rank': card.rank, 'suit': card.suit})

        handData['satOut'] = True
        handData['burnedCards'] = burnedCards
        handData['bankrollAfter'] = game.bankroll
        handData['profit'] = 0

        gameHistory.append(handData)

        return jsonify({
            'success': True,
            'satOut': True,
            'handData': handData,
            'stats': getStats()
        })

    # Play the hand
    betAmount = game.bankrollManager.getBetAmount(trueCount, game.bankroll) if game.useCardCounting else game.baseBet
    handData['bet'] = betAmount
    handData['betMultiplier'] = betAmount / game.baseBet

    # Deal cards
    playerHand = []
    dealerHand = []

    for _ in range(2):
        card = game.deck.dealCard()
        game.counter.countCard(card)
        playerHand.append({'rank': card.rank, 'suit': card.suit})

        card = game.deck.dealCard()
        game.counter.countCard(card)
        dealerHand.append({'rank': card.rank, 'suit': card.suit})

    handData['playerHand'] = playerHand
    handData['dealerHand'] = dealerHand
    handData['dealerUpcard'] = dealerHand[0]

    # Calculate hand values
    playerValue = calculateHandValue(playerHand)
    dealerValue = calculateHandValue([dealerHand[0]])

    handData['playerValue'] = playerValue

    # Check for blackjacks
    playerBlackjack = len(playerHand) == 2 and playerValue == 21
    dealerBlackjack = len(dealerHand) == 2 and calculateHandValue(dealerHand) == 21

    if playerBlackjack or dealerBlackjack:
        if playerBlackjack and dealerBlackjack:
            result = 'push'
            profit = 0
            game.handsPushed += 1
        elif playerBlackjack:
            result = 'playerBlackjack'
            profit = betAmount * 1.5
            game.bankroll += profit
            game.handsWon += 1
        else:
            result = 'dealerBlackjack'
            profit = -betAmount
            game.bankroll -= betAmount
            game.handsLost += 1

        game.handsPlayed += 1
        game.totalWagered += betAmount
        game.updateBankrollStats()

        handData['result'] = result
        handData['profit'] = profit
        handData['bankrollAfter'] = game.bankroll
        handData['dealerValue'] = calculateHandValue(dealerHand)

        gameHistory.append(handData)

        return jsonify({
            'success': True,
            'handData': handData,
            'stats': getStats()
        })

    # Player plays using basic strategy
    actions = []
    playerCards = [Card(c['rank'], c['suit']) for c in playerHand]
    dealerUpcard = Card(dealerHand[0]['rank'], dealerHand[0]['suit'])

    tempHand = Hand()
    for card in playerCards:
        tempHand.addCard(card)
    tempHand.betAmount = betAmount

    while True:
        canDouble = len(tempHand.cards) == 2 and game.bankroll >= tempHand.betAmount
        action = BasicStrategy.getAction(tempHand, dealerUpcard, canDouble, False)

        actions.append(action.value)

        if action.value == "Hit":
            card = game.deck.dealCard()
            game.counter.countCard(card)
            tempHand.addCard(card)
            playerHand.append({'rank': card.rank, 'suit': card.suit})

            if tempHand.isBusted():
                game.bankroll -= betAmount
                game.handsLost += 1
                game.handsPlayed += 1
                game.totalWagered += betAmount
                game.updateBankrollStats()

                handData['playerHand'] = playerHand
                handData['playerValue'] = tempHand.getValue()
                handData['actions'] = actions
                handData['result'] = 'playerBust'
                handData['profit'] = -betAmount
                handData['bankrollAfter'] = game.bankroll

                gameHistory.append(handData)

                return jsonify({
                    'success': True,
                    'handData': handData,
                    'stats': getStats()
                })

        elif action.value == "Stand":
            break

        elif action.value == "Double Down":
            if canDouble:
                tempHand.betAmount *= 2
                betAmount *= 2
                card = game.deck.dealCard()
                game.counter.countCard(card)
                tempHand.addCard(card)
                playerHand.append({'rank': card.rank, 'suit': card.suit})

                if tempHand.isBusted():
                    game.bankroll -= betAmount
                    game.handsLost += 1
                    game.handsPlayed += 1
                    game.totalWagered += betAmount
                    game.updateBankrollStats()

                    handData['playerHand'] = playerHand
                    handData['playerValue'] = tempHand.getValue()
                    handData['actions'] = actions
                    handData['result'] = 'playerBust'
                    handData['profit'] = -betAmount
                    handData['bankrollAfter'] = game.bankroll
                    handData['bet'] = betAmount

                    gameHistory.append(handData)

                    return jsonify({
                        'success': True,
                        'handData': handData,
                        'stats': getStats()
                    })
                break
            else:
                # Can't double, hit instead
                card = game.deck.dealCard()
                game.counter.countCard(card)
                tempHand.addCard(card)
                playerHand.append({'rank': card.rank, 'suit': card.suit})

                if tempHand.isBusted():
                    game.bankroll -= betAmount
                    game.handsLost += 1
                    game.handsPlayed += 1
                    game.totalWagered += betAmount
                    game.updateBankrollStats()

                    handData['playerHand'] = playerHand
                    handData['playerValue'] = tempHand.getValue()
                    handData['actions'] = actions
                    handData['result'] = 'playerBust'
                    handData['profit'] = -betAmount
                    handData['bankrollAfter'] = game.bankroll

                    gameHistory.append(handData)

                    return jsonify({
                        'success': True,
                        'handData': handData,
                        'stats': getStats()
                    })

    # Dealer plays
    dealerCards = [Card(c['rank'], c['suit']) for c in dealerHand]
    tempDealerHand = Hand()
    for card in dealerCards:
        tempDealerHand.addCard(card)

    while tempDealerHand.getValue() < 17:
        card = game.deck.dealCard()
        game.counter.countCard(card)
        tempDealerHand.addCard(card)
        dealerHand.append({'rank': card.rank, 'suit': card.suit})

    # Determine winner
    playerValue = tempHand.getValue()
    dealerValue = tempDealerHand.getValue()

    if tempDealerHand.isBusted() or playerValue > dealerValue:
        result = 'playerWin'
        profit = betAmount
        game.bankroll += betAmount
        game.handsWon += 1
    elif playerValue < dealerValue:
        result = 'dealerWin'
        profit = -betAmount
        game.bankroll -= betAmount
        game.handsLost += 1
    else:
        result = 'push'
        profit = 0
        game.handsPushed += 1

    game.handsPlayed += 1
    game.totalWagered += betAmount
    game.updateBankrollStats()

    handData['playerHand'] = playerHand
    handData['dealerHand'] = dealerHand
    handData['playerValue'] = playerValue
    handData['dealerValue'] = dealerValue
    handData['actions'] = actions
    handData['result'] = result
    handData['profit'] = profit
    handData['bankrollAfter'] = game.bankroll
    handData['bet'] = betAmount

    gameHistory.append(handData)

    return jsonify({
        'success': True,
        'handData': handData,
        'stats': getStats()
    })


@app.route('/api/stats', methods=['GET'])
def stats():
    """Get current game statistics"""
    return jsonify(getStats())


@app.route('/api/history', methods=['GET'])
def history():
    """Get game history"""
    return jsonify({
        'history': gameHistory
    })


def getStats():
    """Helper to get current statistics"""
    if game is None:
        return {}

    profit = game.bankroll - 1000.0
    roi = (profit / game.totalWagered * 100) if game.totalWagered > 0 else 0

    totalOpportunities = game.handsPlayed + game.handsSatOut

    return {
        'handsPlayed': game.handsPlayed,
        'handsSatOut': game.handsSatOut,
        'totalOpportunities': totalOpportunities,
        'handsWon': game.handsWon,
        'handsLost': game.handsLost,
        'handsPushed': game.handsPushed,
        'bankroll': game.bankroll,
        'profit': profit,
        'roi': roi,
        'totalWagered': game.totalWagered,
        'maxBankroll': game.maxBankroll,
        'minBankroll': game.minBankroll,
        'runningCount': game.counter.runningCount,
        'trueCount': game.counter.getTrueCount(game.deck.decksRemaining()),
        'decksRemaining': game.deck.decksRemaining()
    }


def calculateHandValue(hand):
    """Calculate the value of a hand"""
    total = 0
    aces = 0

    for card in hand:
        rank = card['rank']
        if rank in ['J', 'Q', 'K']:
            total += 10
        elif rank == 'A':
            total += 11
            aces += 1
        else:
            total += int(rank)

    while total > 21 and aces > 0:
        total -= 10
        aces -= 1

    return total


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("BLACKJACK AI - WEB INTERFACE")
    print("=" * 60)
    print("\nStarting server...")
    print("Open your browser to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)