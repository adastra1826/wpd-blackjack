#!/usr/bin/env python3
"""
Basic Strategy for Blackjack
Implements standard basic strategy based on player hand and dealer upcard
"""

class Strategy:
    """Basic Strategy implementation"""
    
    def __init__(self):
        # Define basic strategy tables
        # H = Hit, S = Stand, D = Double (if allowed, else hit), P = Split
        
        # Hard totals (no ace or ace counted as 1)
        self.hard_strategy = {
            # Player total: {dealer_upcard: action}
            21: {2:'S', 3:'S', 4:'S', 5:'S', 6:'S', 7:'S', 8:'S', 9:'S', 10:'S', 11:'S'},
            20: {2:'S', 3:'S', 4:'S', 5:'S', 6:'S', 7:'S', 8:'S', 9:'S', 10:'S', 11:'S'},
            19: {2:'S', 3:'S', 4:'S', 5:'S', 6:'S', 7:'S', 8:'S', 9:'S', 10:'S', 11:'S'},
            18: {2:'S', 3:'S', 4:'S', 5:'S', 6:'S', 7:'S', 8:'S', 9:'S', 10:'S', 11:'S'},
            17: {2:'S', 3:'S', 4:'S', 5:'S', 6:'S', 7:'S', 8:'S', 9:'S', 10:'S', 11:'S'},
            16: {2:'S', 3:'S', 4:'S', 5:'S', 6:'S', 7:'H', 8:'H', 9:'H', 10:'H', 11:'H'},
            15: {2:'S', 3:'S', 4:'S', 5:'S', 6:'S', 7:'H', 8:'H', 9:'H', 10:'H', 11:'H'},
            14: {2:'S', 3:'S', 4:'S', 5:'S', 6:'S', 7:'H', 8:'H', 9:'H', 10:'H', 11:'H'},
            13: {2:'S', 3:'S', 4:'S', 5:'S', 6:'S', 7:'H', 8:'H', 9:'H', 10:'H', 11:'H'},
            12: {2:'H', 3:'H', 4:'S', 5:'S', 6:'S', 7:'H', 8:'H', 9:'H', 10:'H', 11:'H'},
            11: {2:'D', 3:'D', 4:'D', 5:'D', 6:'D', 7:'D', 8:'D', 9:'D', 10:'D', 11:'H'},
            10: {2:'D', 3:'D', 4:'D', 5:'D', 6:'D', 7:'D', 8:'D', 9:'D', 10:'H', 11:'H'},
            9:  {2:'H', 3:'D', 4:'D', 5:'D', 6:'D', 7:'H', 8:'H', 9:'H', 10:'H', 11:'H'},
            8:  {2:'H', 3:'H', 4:'H', 5:'H', 6:'H', 7:'H', 8:'H', 9:'H', 10:'H', 11:'H'},
            7:  {2:'H', 3:'H', 4:'H', 5:'H', 6:'H', 7:'H', 8:'H', 9:'H', 10:'H', 11:'H'},
            6:  {2:'H', 3:'H', 4:'H', 5:'H', 6:'H', 7:'H', 8:'H', 9:'H', 10:'H', 11:'H'},
            5:  {2:'H', 3:'H', 4:'H', 5:'H', 6:'H', 7:'H', 8:'H', 9:'H', 10:'H', 11:'H'},
        }
        
        # Soft totals (ace counted as 11)
        self.soft_strategy = {
            # A,9 (20)
            20: {2:'S', 3:'S', 4:'S', 5:'S', 6:'S', 7:'S', 8:'S', 9:'S', 10:'S', 11:'S'},
            # A,8 (19)
            19: {2:'S', 3:'S', 4:'S', 5:'S', 6:'S', 7:'S', 8:'S', 9:'S', 10:'S', 11:'S'},
            # A,7 (18)
            18: {2:'S', 3:'D', 4:'D', 5:'D', 6:'D', 7:'S', 8:'S', 9:'H', 10:'H', 11:'H'},
            # A,6 (17)
            17: {2:'H', 3:'D', 4:'D', 5:'D', 6:'D', 7:'H', 8:'H', 9:'H', 10:'H', 11:'H'},
            # A,5 (16)
            16: {2:'H', 3:'H', 4:'D', 5:'D', 6:'D', 7:'H', 8:'H', 9:'H', 10:'H', 11:'H'},
            # A,4 (15)
            15: {2:'H', 3:'H', 4:'D', 5:'D', 6:'D', 7:'H', 8:'H', 9:'H', 10:'H', 11:'H'},
            # A,3 (14)
            14: {2:'H', 3:'H', 4:'H', 5:'D', 6:'D', 7:'H', 8:'H', 9:'H', 10:'H', 11:'H'},
            # A,2 (13)
            13: {2:'H', 3:'H', 4:'H', 5:'D', 6:'D', 7:'H', 8:'H', 9:'H', 10:'H', 11:'H'},
        }
        
        # Pair splitting strategy
        self.split_strategy = {
            # Pair value: {dealer_upcard: action}
            11: {2:'P', 3:'P', 4:'P', 5:'P', 6:'P', 7:'P', 8:'P', 9:'P', 10:'P', 11:'P'},  # AA
            10: {2:'S', 3:'S', 4:'S', 5:'S', 6:'S', 7:'S', 8:'S', 9:'S', 10:'S', 11:'S'},  # TT
            9:  {2:'P', 3:'P', 4:'P', 5:'P', 6:'P', 7:'S', 8:'P', 9:'P', 10:'S', 11:'S'},  # 99
            8:  {2:'P', 3:'P', 4:'P', 5:'P', 6:'P', 7:'P', 8:'P', 9:'P', 10:'P', 11:'P'},  # 88
            7:  {2:'P', 3:'P', 4:'P', 5:'P', 6:'P', 7:'P', 8:'H', 9:'H', 10:'H', 11:'H'},  # 77
            6:  {2:'P', 3:'P', 4:'P', 5:'P', 6:'P', 7:'H', 8:'H', 9:'H', 10:'H', 11:'H'},  # 66
            5:  {2:'S', 3:'S', 4:'S', 5:'S', 6:'S', 7:'S', 8:'S', 9:'S', 10:'S', 11:'S'},  # 55 (treat as 10)
            4:  {2:'H', 3:'H', 4:'H', 5:'P', 6:'P', 7:'H', 8:'H', 9:'H', 10:'H', 11:'H'},  # 44
            3:  {2:'P', 3:'P', 4:'P', 5:'P', 6:'P', 7:'P', 8:'H', 9:'H', 10:'H', 11:'H'},  # 33
            2:  {2:'P', 3:'P', 4:'P', 5:'P', 6:'P', 7:'P', 8:'H', 9:'H', 10:'H', 11:'H'},  # 22
        }
    
    def parse_card(self, card_str):
        """Parse card string into value"""
        if card_str == '?':
            return 0
        
        rank = card_str[0]
        if rank == 'A':
            return 11
        elif rank in ['K', 'Q', 'J', 'X']:
            return 10
        else:
            return int(rank)
    
    def is_soft_hand(self, cards):
        """Check if hand is soft (has ace counted as 11)"""
        values = [self.parse_card(card) for card in cards]
        has_ace = 11 in values
        
        if has_ace:
            total = sum(values)
            # If total is 21 or less with ace as 11, it's soft
            return total <= 21
        return False
    
    def is_pair(self, cards):
        """Check if hand is a pair"""
        if len(cards) != 2:
            return False
        
        val1 = self.parse_card(cards[0])
        val2 = self.parse_card(cards[1])
        return val1 == val2
    
    def get_action(self, player_value, dealer_value, available_actions, is_split=False, cards=None):
        """
        Get recommended action based on basic strategy
        
        Args:
            player_value: Current hand value
            dealer_value: Dealer's upcard value
            available_actions: List of available actions
            is_split: Whether this is a split hand
            cards: Player's cards (for determining soft hands and pairs)
        
        Returns:
            Recommended action string
        """
        
        # Convert dealer value (handle ace as 11)
        if dealer_value == 0:
            return 'none'
        
        # Map actions to our internal representation
        action_map = {
            'H': 'hit',
            'S': 'stay',
            'D': 'double',
            'P': 'split',
        }
        
        # Handle split hands
        if is_split:
            if 'HIT_SPLIT' in available_actions:
                action_map['H'] = 'hit_split'
            if 'STAY_SPLIT' in available_actions:
                action_map['S'] = 'stay_split'
        
        # Check for pairs (only if split is available)
        if cards and len(cards) == 2 and 'SPLIT' in available_actions and not is_split:
            if self.is_pair(cards):
                pair_value = self.parse_card(cards[0])
                if pair_value in self.split_strategy:
                    if dealer_value in self.split_strategy[pair_value]:
                        recommended = self.split_strategy[pair_value][dealer_value]
                        if recommended == 'P':
                            return 'split'
        
        # Check for soft hands
        if cards and self.is_soft_hand(cards):
            if player_value in self.soft_strategy:
                if dealer_value in self.soft_strategy[player_value]:
                    recommended = self.soft_strategy[player_value][dealer_value]
                    
                    # Convert to available action
                    if recommended == 'D':
                        if 'DOUBLE_DOWN' in available_actions and not is_split:
                            return 'double'
                        else:
                            recommended = 'H'  # Hit if can't double
                    
                    return action_map.get(recommended, 'hit')
        
        # Hard totals
        if player_value >= 21:
            return 'stay' if not is_split else 'stay_split'
        elif player_value < 5:
            return 'hit' if not is_split else 'hit_split'
        elif player_value in self.hard_strategy:
            if dealer_value in self.hard_strategy[player_value]:
                recommended = self.hard_strategy[player_value][dealer_value]
                
                # Convert to available action
                if recommended == 'D':
                    if 'DOUBLE_DOWN' in available_actions and not is_split:
                        return 'double'
                    else:
                        recommended = 'H'  # Hit if can't double
                
                return action_map.get(recommended, 'hit')
        
        # Default action
        if player_value >= 17:
            return 'stay' if not is_split else 'stay_split'
        else:
            return 'hit' if not is_split else 'hit_split'
    
    def should_take_insurance(self, player_cards):
        """
        Determine if insurance should be taken
        Basic strategy: Never take insurance
        """
        return False