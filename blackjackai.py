"""
Blackjack AI with Card Counting - Senior Project
This AI plays blackjack using basic strategy AND counts cards to increase bets when the deck is favorable
"""

import random
from enum import Enum
from typing import List, Tuple, Optional


class Action(Enum):
    """What the player can do"""
    HIT = "Hit"
    STAND = "Stand"
    DOUBLE = "Double Down"
    SPLIT = "Split"


class Card:
    """A single playing card"""
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    SUITS = ['♠', '♥', '♦', '♣']

    def __init__(self, rank: str, suit: str):
        self.rank = rank
        self.suit = suit

    def getValue(self) -> int:
        # Face cards are worth 10
        if self.rank in ['J', 'Q', 'K']:
            return 10
        # Aces start at 11 (we adjust later if needed)
        elif self.rank == 'A':
            return 11
        else:
            return int(self.rank)

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"

    def __repr__(self) -> str:
        return str(self)


class Deck:
    """Multi-deck shoe used in casinos"""

    def __init__(self, numDecks: int = 6):
        self.numDecks = numDecks
        self.cards: List[Card] = []
        self.totalCards = numDecks * 52
        self.reset()

    def reset(self):
        # Build a fresh shoe with multiple decks
        self.cards = []
        for i in range(self.numDecks):
            for suit in Card.SUITS:
                for rank in Card.RANKS:
                    self.cards.append(Card(rank, suit))
        # Shuffle the whole shoe
        random.shuffle(self.cards)

    def dealCard(self) -> Card:
        # Take the top card off the deck
        return self.cards.pop()

    def cardsRemaining(self) -> int:
        return len(self.cards)

    def decksRemaining(self) -> float:
        # How many full decks are left? Important for true count calculation
        return len(self.cards) / 52.0

    def needsReshuffle(self, reshufflePoint: int) -> bool:
        # Check if we've hit the cut card (penetration point)
        return len(self.cards) < reshufflePoint


class Hand:
    """A blackjack hand - can be player or dealer"""

    def __init__(self):
        self.cards: List[Card] = []
        self.betAmount: float = 0
        self.isDoubled: bool = False
        self.wasSplit: bool = False

    def addCard(self, card: Card):
        self.cards.append(card)

    def getValue(self) -> int:
        # Calculate hand value, adjusting for aces
        totalValue = sum(card.getValue() for card in self.cards)
        numAces = sum(1 for card in self.cards if card.rank == 'A')

        # If we bust, start counting aces as 1 instead of 11
        while totalValue > 21 and numAces > 0:
            totalValue -= 10
            numAces -= 1

        return totalValue

    def isSoft(self) -> bool:
        # A "soft" hand has an ace counted as 11
        totalValue = sum(card.getValue() for card in self.cards)
        numAces = sum(1 for card in self.cards if card.rank == 'A')

        # If we have an ace and aren't busted, it's soft
        return numAces > 0 and totalValue <= 21

    def isBlackjack(self) -> bool:
        # Natural 21 with first two cards
        return len(self.cards) == 2 and self.getValue() == 21

    def isBusted(self) -> bool:
        return self.getValue() > 21

    def canSplit(self) -> bool:
        # Can only split pairs
        return len(self.cards) == 2 and self.cards[0].getValue() == self.cards[1].getValue()

    def __str__(self) -> str:
        cardsString = ', '.join(str(card) for card in self.cards)
        return f"{cardsString} (Value: {self.getValue()})"


class CardCounter:
    """
    Hi-Lo card counting system - the most popular counting method

    The basic idea: Low cards (2-6) help the dealer, high cards (10-A) help the player
    So we track when the deck has more high cards left (good for us!)
    """

    def __init__(self):
        self.runningCount = 0
        self.cardsSeen = 0

    def countCard(self, card: Card) -> int:
        """
        Update the count based on what card we see

        Hi-Lo system:
        +1 for low cards (2,3,4,5,6) - BAD cards for player
        0 for neutral (7,8,9)
        -1 for high cards (10,J,Q,K,A) - GOOD cards for player

        So POSITIVE count = lots of low cards gone = deck is rich in high cards = GOOD FOR US
        """
        cardValue = card.getValue()
        rank = card.rank

        # Low cards leaving the deck is GOOD for player
        if rank in ['2', '3', '4', '5', '6']:
            countValue = 1
        # Neutral cards don't matter
        elif rank in ['7', '8', '9']:
            countValue = 0
        # High cards leaving is BAD for player
        else:  # 10, J, Q, K, A
            countValue = -1

        self.runningCount += countValue
        self.cardsSeen += 1
        return countValue

    def getTrueCount(self, decksRemaining: float) -> float:
        """
        True count = running count / decks remaining

        This is MORE ACCURATE than running count because it accounts for how much
        of the shoe is left. A running count of +6 with 1 deck left is MUCH better
        than a running count of +6 with 4 decks left!
        """
        if decksRemaining <= 0:
            return 0
        return self.runningCount / decksRemaining

    def reset(self):
        # New shoe, reset everything
        self.runningCount = 0
        self.cardsSeen = 0


class BankrollManager:
    """
    Manages bet sizing based on the count

    Basic principle: Bet more when count is high (deck favors us)
                    Bet minimum when count is low or negative
    """

    def __init__(self, baseBet: float = 10.0, maxBetMultiplier: float = 10.0):
        self.baseBet = baseBet
        self.maxBetMultiplier = maxBetMultiplier

    def getBetAmount(self, trueCount: float, currentBankroll: float) -> float:
        """
        Calculate how much to bet based on true count

        Betting spread based on TRUE COUNT:
        TC < 1: Min bet (1x)
        TC = 1: 2x
        TC = 2: 4x
        TC = 3: 6x
        TC >= 4: 8x

        This is aggressive but not TOO obvious to casino surveillance
        """

        # Determine multiplier from true count
        if trueCount < 1:
            multiplier = 1  # Min bet when count is bad
        elif trueCount < 2:
            multiplier = 2
        elif trueCount < 3:
            multiplier = 4  # Now we're getting somewhere!
        elif trueCount < 4:
            multiplier = 6
        else:
            multiplier = 8  # BIG BET TERRITORY

        # Don't go overboard
        multiplier = min(multiplier, self.maxBetMultiplier)

        # Calculate actual bet
        betAmount = self.baseBet * multiplier

        # BANKROLL MANAGEMENT - never risk more than 5% of roll on one hand
        maxAllowedBet = currentBankroll * 0.05
        betAmount = min(betAmount, maxAllowedBet)

        # Make sure we can actually afford it
        betAmount = min(betAmount, currentBankroll)

        # Never go below minimum bet
        return max(self.baseBet, betAmount)


class BasicStrategy:
    """
    Optimal basic strategy - this is the mathematically correct play for every situation
    Developed through millions of computer simulations
    """

    @staticmethod
    def getAction(playerHand: Hand, dealerUpcard: Card, canDouble: bool = True, canSplit: bool = True) -> Action:
        """
        Returns the optimal play based on our hand and dealer's upcard

        This is "the book" - basic strategy doesn't care about the count,
        just the current situation
        """
        playerValue = playerHand.getValue()
        dealerValue = dealerUpcard.getValue()

        # Check if we should split pairs first
        if canSplit and playerHand.canSplit():
            return BasicStrategy.pairSplittingStrategy(playerHand, dealerValue)

        # Soft hands (have an ace counted as 11)
        if playerHand.isSoft() and len(playerHand.cards) == 2:
            return BasicStrategy.softHandStrategy(playerValue, dealerValue, canDouble)

        # Hard hands (no ace, or ace counted as 1)
        return BasicStrategy.hardHandStrategy(playerValue, dealerValue, canDouble)

    @staticmethod
    def pairSplittingStrategy(playerHand: Hand, dealerValue: int) -> Action:
        # What to do with pairs
        cardValue = playerHand.cards[0].getValue()

        # ALWAYS split aces and 8s - these are the golden rules
        if cardValue == 11 or cardValue == 8:
            return Action.SPLIT

        # NEVER split 5s or 10s - terrible idea
        if cardValue == 5 or cardValue == 10:
            return BasicStrategy.hardHandStrategy(playerHand.getValue(), dealerValue, True)

        # Split 2s, 3s, 7s against weak dealer cards
        if cardValue in [2, 3, 7]:
            if 2 <= dealerValue <= 7:
                return Action.SPLIT

        # Split 4s only against dealer 5-6
        if cardValue == 4:
            if 5 <= dealerValue <= 6:
                return Action.SPLIT

        # Split 6s against dealer 2-6
        if cardValue == 6:
            if 2 <= dealerValue <= 6:
                return Action.SPLIT

        # Split 9s except against dealer 7, 10, or ace
        if cardValue == 9:
            if (2 <= dealerValue <= 6) or (8 <= dealerValue <= 9):
                return Action.SPLIT

        # If not splitting, play as hard hand
        return BasicStrategy.hardHandStrategy(playerHand.getValue(), dealerValue, True)

    @staticmethod
    def softHandStrategy(playerValue: int, dealerValue: int, canDouble: bool) -> Action:
        # Strategy for soft hands (ace as 11)

        # Soft 19+ is strong - stand
        if playerValue >= 19:
            return Action.STAND

        # Soft 18 is tricky - depends on dealer
        if playerValue == 18:
            if canDouble and dealerValue in [3, 4, 5, 6]:
                return Action.DOUBLE  # Double against weak dealer
            elif dealerValue in [2, 7, 8]:
                return Action.STAND
            else:
                return Action.HIT  # Hit against strong dealer

        # Soft 17 - double against dealer 3-6
        if playerValue == 17:
            if canDouble and dealerValue in [3, 4, 5, 6]:
                return Action.DOUBLE
            else:
                return Action.HIT

        # Soft 15-16 - double against 4-6
        if playerValue in [15, 16]:
            if canDouble and dealerValue in [4, 5, 6]:
                return Action.DOUBLE
            else:
                return Action.HIT

        # Soft 13-14 - double against 5-6
        if playerValue in [13, 14]:
            if canDouble and dealerValue in [5, 6]:
                return Action.DOUBLE
            else:
                return Action.HIT

        return Action.HIT

    @staticmethod
    def hardHandStrategy(playerValue: int, dealerValue: int, canDouble: bool) -> Action:
        # Strategy for hard hands (no soft ace)

        # 17+ always stand
        if playerValue >= 17:
            return Action.STAND

        # 13-16 is the "danger zone" - stand against weak dealer, hit against strong
        if 13 <= playerValue <= 16:
            if 2 <= dealerValue <= 6:
                return Action.STAND  # Dealer might bust
            else:
                return Action.HIT  # Gotta take our chances

        # 12 against dealer 4-6
        if playerValue == 12:
            if 4 <= dealerValue <= 6:
                return Action.STAND
            else:
                return Action.HIT

        # 11 is the BEST doubling hand
        if playerValue == 11:
            if canDouble:
                return Action.DOUBLE
            else:
                return Action.HIT

        # 10 is also great for doubling (except against dealer 10 or ace)
        if playerValue == 10:
            if canDouble and dealerValue <= 9:
                return Action.DOUBLE
            else:
                return Action.HIT

        # 9 against weak dealer 3-6
        if playerValue == 9:
            if canDouble and 3 <= dealerValue <= 6:
                return Action.DOUBLE
            else:
                return Action.HIT

        # Anything 8 or less - always hit
        return Action.HIT


class BlackjackGame:
    """Main game engine with card counting and bankroll management"""

    def __init__(self, startingBankroll: float = 1000.0, baseBet: float = 10.0,
                 useCardCounting: bool = True, penetration: float = 0.75,
                 useWonging: bool = True, wongingThreshold: float = -1.0):
        """
        Set up the game

        Args:
            startingBankroll: How much money we start with
            baseBet: Minimum bet (what we bet when count is bad)
            useCardCounting: Turn card counting on/off
            penetration: How far into the deck before reshuffling (0.75 = 75% of cards dealt)
            useWonging: Whether to use Wonging (sitting out unfavorable counts)
            wongingThreshold: True count below which we sit out (default: -1.0)
        """
        self.deck = Deck(numDecks=6)  # Standard 6-deck shoe
        self.bankroll = startingBankroll
        self.baseBet = baseBet
        self.useCardCounting = useCardCounting
        self.useWonging = useWonging
        self.wongingThreshold = wongingThreshold
        self.penetration = penetration

        # Calculate when to reshuffle (penetration point)
        self.reshufflePoint = int(self.deck.numDecks * 52 * (1 - penetration))

        # Initialize card counting system
        self.counter = CardCounter()
        self.bankrollManager = BankrollManager(baseBet=baseBet, maxBetMultiplier=10.0)

        # Track statistics
        self.handsPlayed = 0
        self.handsWon = 0
        self.handsLost = 0
        self.handsPushed = 0
        self.handsSatOut = 0  # NEW: Track hands we skipped
        self.totalWagered = 0.0
        self.maxBankroll = startingBankroll
        self.minBankroll = startingBankroll

    def playHand(self, verbose: bool = True) -> float:
        """
        Play one hand of blackjack with card counting and optional Wonging

        Returns the profit or loss for this hand (0 if sitting out)
        """

        # Check if we need to reshuffle the shoe
        if self.deck.needsReshuffle(self.reshufflePoint):
            if verbose:
                print(f"\n{'~'*60}")
                print("RESHUFFLING DECK - Count reset to 0")
                print(f"{'~'*60}")
            self.deck.reset()
            self.counter.reset()

        # Calculate true count and determine if we should play this hand
        trueCount = self.counter.getTrueCount(self.deck.decksRemaining())

        # WONGING: Sit out if count is too unfavorable
        if self.useWonging and trueCount < self.wongingThreshold:
            self.handsSatOut += 1
            if verbose:
                print(f"\n{'='*60}")
                print(f"Hand #{self.handsPlayed + self.handsSatOut}")
                print(f"{'='*60}")
                print(f"Running Count: {self.counter.runningCount:+d} | True Count: {trueCount:+.1f}")
                print(f"Count too negative - SITTING OUT this hand")
                print(f"(Wonging threshold: {self.wongingThreshold:+.1f})")

            # Still need to "see" the cards to maintain count accuracy
            # Deal cards face up but don't play
            burnCards = []
            for _ in range(4):  # Typical hand uses ~4 cards
                if len(self.deck.cards) > 0:
                    card = self.deck.dealCard()
                    self.counter.countCard(card)
                    burnCards.append(card)

            if verbose and len(burnCards) > 0:
                print(f"Cards seen: {', '.join(str(c) for c in burnCards)}")

            return 0.0

        # Determine bet size based on count
        if self.useCardCounting:
            betAmount = self.bankrollManager.getBetAmount(trueCount, self.bankroll)
        else:
            betAmount = self.baseBet

        # Check if we're broke
        if self.bankroll < betAmount:
            if verbose:
                print("OUT OF MONEY!")
            return 0.0

        # Deal the initial cards
        playerHand = Hand()
        dealerHand = Hand()
        playerHand.betAmount = betAmount

        # Deal 2 cards to player, 2 to dealer (alternating)
        for i in range(2):
            card = self.deck.dealCard()
            playerHand.addCard(card)
            self.counter.countCard(card)  # Count every card we see

            card = self.deck.dealCard()
            dealerHand.addCard(card)
            self.counter.countCard(card)

        if verbose:
            print(f"\n{'='*60}")
            print(f"Hand #{self.handsPlayed + 1}")
            print(f"{'='*60}")
            print(f"Bankroll: ${self.bankroll:.2f}")

            if self.useCardCounting:
                print(f"Running Count: {self.counter.runningCount:+d} | True Count: {trueCount:+.1f}")
                print(f"Decks Remaining: {self.deck.decksRemaining():.1f}")

            betMultiplier = f" ({betAmount/self.baseBet:.0f}x base bet)" if betAmount != self.baseBet else ""
            print(f"Bet: ${betAmount:.2f}{betMultiplier}")
            print(f"\nPlayer hand: {playerHand}")
            print(f"Dealer shows: {dealerHand.cards[0]}")

        # Track total amount wagered for statistics
        self.totalWagered += betAmount

        # Check for natural blackjacks
        if playerHand.isBlackjack():
            if dealerHand.isBlackjack():
                # Both have blackjack - push (tie)
                if verbose:
                    print("\nBoth have blackjack - PUSH!")
                self.handsPushed += 1
                self.handsPlayed += 1
                return 0.0
            else:
                # Player blackjack wins 3:2
                profit = betAmount * 1.5
                self.bankroll += profit
                self.handsWon += 1
                self.handsPlayed += 1
                self.updateBankrollStats()
                if verbose:
                    print("\nBLACKJACK! Wins 3:2")
                    print(f"Profit: ${profit:.2f}")
                return profit
        elif dealerHand.isBlackjack():
            # Dealer blackjack, player loses
            self.bankroll -= betAmount
            self.handsLost += 1
            self.handsPlayed += 1
            self.updateBankrollStats()
            if verbose:
                print(f"\nDealer blackjack! Dealer hand: {dealerHand}")
                print(f"Loss: ${betAmount:.2f}")
            return -betAmount

        # Play player's hand using basic strategy
        result = self.playPlayerHand(playerHand, dealerHand.cards[0], verbose)

        if result is not None:
            # Hand ended early (player busted)
            self.handsPlayed += 1
            self.updateBankrollStats()
            return result

        # Now dealer plays
        if verbose:
            print(f"\nDealer's turn...")
            print(f"Dealer hand: {dealerHand}")

        # Dealer must hit on 16 or less, stand on 17+
        while dealerHand.getValue() < 17:
            card = self.deck.dealCard()
            dealerHand.addCard(card)
            self.counter.countCard(card)  # Keep counting
            if verbose:
                print(f"Dealer hits: {card}")
                print(f"Dealer hand: {dealerHand}")

        if dealerHand.isBusted():
            if verbose:
                print(f"Dealer busts!")

        # Compare hands and determine winner
        profit = self.determineWinner(playerHand, dealerHand, verbose)
        self.handsPlayed += 1
        self.updateBankrollStats()

        return profit

    def playPlayerHand(self, playerHand: Hand, dealerUpcard: Card, verbose: bool) -> Optional[float]:
        """
        Play the player's hand according to basic strategy

        Returns profit/loss if hand ends, None if dealer needs to play
        """
        while True:
            # Can we double? Only on first two cards and if we have enough money
            canDouble = len(playerHand.cards) == 2 and self.bankroll >= playerHand.betAmount

            # Get the optimal play from basic strategy
            action = BasicStrategy.getAction(playerHand, dealerUpcard, canDouble, False)

            if verbose:
                print(f"\nAction: {action.value}")

            if action == Action.HIT:
                card = self.deck.dealCard()
                playerHand.addCard(card)
                self.counter.countCard(card)
                if verbose:
                    print(f"Player hits: {card}")
                    print(f"Player hand: {playerHand}")

                # Check for bust
                if playerHand.isBusted():
                    self.bankroll -= playerHand.betAmount
                    self.handsLost += 1
                    if verbose:
                        print(f"\nBUST! Loss: ${playerHand.betAmount:.2f}")
                    return -playerHand.betAmount

            elif action == Action.STAND:
                if verbose:
                    print("Player stands")
                return None  # Dealer's turn now

            elif action == Action.DOUBLE:
                if canDouble:
                    # Double the bet and take ONE more card
                    playerHand.isDoubled = True
                    playerHand.betAmount *= 2
                    card = self.deck.dealCard()
                    playerHand.addCard(card)
                    self.counter.countCard(card)
                    if verbose:
                        print(f"Player doubles down: {card}")
                        print(f"Player hand: {playerHand}")

                    # Check for bust
                    if playerHand.isBusted():
                        self.bankroll -= playerHand.betAmount
                        self.handsLost += 1
                        if verbose:
                            print(f"\nBUST! Loss: ${playerHand.betAmount:.2f}")
                        return -playerHand.betAmount

                    return None  # Dealer's turn
                else:
                    # Can't double, so just hit instead
                    card = self.deck.dealCard()
                    playerHand.addCard(card)
                    self.counter.countCard(card)
                    if verbose:
                        print(f"Player hits (can't double): {card}")
                        print(f"Player hand: {playerHand}")

                    if playerHand.isBusted():
                        self.bankroll -= playerHand.betAmount
                        self.handsLost += 1
                        if verbose:
                            print(f"\nBUST! Loss: ${playerHand.betAmount:.2f}")
                        return -playerHand.betAmount

    def determineWinner(self, playerHand: Hand, dealerHand: Hand, verbose: bool) -> float:
        """Compare final hands and update bankroll"""
        playerValue = playerHand.getValue()
        dealerValue = dealerHand.getValue()
        betAmount = playerHand.betAmount

        if dealerHand.isBusted() or playerValue > dealerValue:
            # Player wins!
            self.bankroll += betAmount
            self.handsWon += 1
            if verbose:
                print(f"\nPLAYER WINS! Profit: ${betAmount:.2f}")
            return betAmount
        elif playerValue < dealerValue:
            # Dealer wins
            self.bankroll -= betAmount
            self.handsLost += 1
            if verbose:
                print(f"\nDEALER WINS! Loss: ${betAmount:.2f}")
            return -betAmount
        else:
            # Tie (push)
            self.handsPushed += 1
            if verbose:
                print(f"\nPUSH - It's a tie!")
            return 0.0

    def updateBankrollStats(self):
        # Track highest and lowest bankroll
        self.maxBankroll = max(self.maxBankroll, self.bankroll)
        self.minBankroll = min(self.minBankroll, self.bankroll)

    def printStatistics(self):
        """Print detailed statistics about the session"""
        print(f"\n{'='*60}")
        print("SESSION STATISTICS")
        print(f"{'='*60}")

        if self.useWonging:
            totalOpportunities = self.handsPlayed + self.handsSatOut
            print(f"Total hands dealt: {totalOpportunities}")
            print(f"Hands played: {self.handsPlayed}")
            print(f"Hands sat out (Wonging): {self.handsSatOut} ({self.handsSatOut/totalOpportunities*100:.1f}%)" if totalOpportunities > 0 else "Hands sat out: 0")
        else:
            print(f"Hands played: {self.handsPlayed}")

        if self.handsPlayed > 0:
            winRate = self.handsWon / self.handsPlayed * 100
            lossRate = self.handsLost / self.handsPlayed * 100
            pushRate = self.handsPushed / self.handsPlayed * 100

            print(f"Hands won: {self.handsWon} ({winRate:.1f}%)")
            print(f"Hands lost: {self.handsLost} ({lossRate:.1f}%)")
            print(f"Hands pushed: {self.handsPushed} ({pushRate:.1f}%)")

            print(f"\nFinal bankroll: ${self.bankroll:.2f}")
            print(f"Starting bankroll: $1000.00")
            profit = self.bankroll - 1000.0
            print(f"Total profit/loss: ${profit:+.2f}")
            print(f"Average per hand: ${profit/self.handsPlayed:+.2f}")

            print(f"\nMax bankroll: ${self.maxBankroll:.2f}")
            print(f"Min bankroll: ${self.minBankroll:.2f}")

            if self.totalWagered > 0:
                roi = (profit / self.totalWagered) * 100
                print(f"\nTotal wagered: ${self.totalWagered:.2f}")
                print(f"ROI: {roi:+.2f}%")


def main():
    """Run the blackjack AI simulation"""
    print("=" * 60)
    print("BLACKJACK AI - Card Counting & Basic Strategy")
    print("With WONGING (sitting out unfavorable counts)")
    print("=" * 60)

    # Initialize the game with card counting AND Wonging enabled
    game = BlackjackGame(
        startingBankroll=1000.0,
        baseBet=10.0,
        useCardCounting=True,  # Card counting ON
        useWonging=True,        # Wonging ON - sit out bad counts
        wongingThreshold=-1.0,  # Sit out when true count below -1
        penetration=0.75        # Deal 75% of the shoe before reshuffling
    )

    # Play multiple hands
    numHands = 100
    print(f"\nPlaying up to {numHands} hands with CARD COUNTING and WONGING enabled...")
    print("The AI will SIT OUT when the count is unfavorable (below -1)")
    print("Watch how it only bets when it has the edge!\n")

    # Show detailed output for first 5 hands so you can see it in action
    for i in range(5):
        game.playHand(verbose=True)

    # Play the rest silently for speed
    handsAttempted = 5
    while game.handsPlayed < numHands and handsAttempted < numHands * 3:
        game.playHand(verbose=False)
        handsAttempted += 1

    # Print final statistics
    game.printStatistics()


if __name__ == "__main__":
    main()