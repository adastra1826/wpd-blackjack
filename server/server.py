#!/usr/bin/env python3
"""
Flask server for Blackjack automation
Handles game state analysis and strategy decisions
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
from datetime import datetime
import importlib
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from python.database import Database

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database with environment variable
db_path = os.getenv('BJ_DB_PATH', 'database/blackjack_data.db')
db = Database(db_path)

# Strategy cache
loaded_strategies = {}

def load_strategy(strategy_name):
    """Dynamically load a strategy module"""
    if strategy_name not in loaded_strategies:
        try:
            module = importlib.import_module(f'strategies.{strategy_name}')
            strategy_class = getattr(module, 'Strategy')
            loaded_strategies[strategy_name] = strategy_class()
            logger.info(f"Loaded strategy: {strategy_name}")
        except Exception as e:
            logger.error(f"Failed to load strategy {strategy_name}: {e}")
            # Fall back to basic strategy
            from strategies.basic_strategy import Strategy
            loaded_strategies[strategy_name] = Strategy()
    
    return loaded_strategies[strategy_name]

def parse_card(card_str):
    """Parse card string (e.g., 'KD', '5H', 'AS') into rank and suit"""
    if card_str == '?':
        return None, None
    
    rank = card_str[0]
    suit = card_str[1] if len(card_str) > 1 else None
    
    # Convert face cards to values
    if rank == 'A':
        return 11, suit  # Ace (soft value)
    elif rank in ['K', 'Q', 'J']:
        return 10, suit
    elif rank == 'X':  # 10
        return 10, suit
    else:
        return int(rank), suit

def calculate_hand_value(cards):
    """Calculate the best value for a hand of cards"""
    if not cards or cards == ['?']:
        return 0
    
    total = 0
    aces = 0
    
    for card in cards:
        if card == '?':
            continue
        rank, _ = parse_card(card)
        if rank is None:
            continue
        
        if rank == 11:  # Ace
            aces += 1
            total += 11
        else:
            total += rank
    
    # Adjust for aces
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    
    return total

@app.route('/game_state', methods=['POST'])
def handle_game_state():
    """Receive game state and return recommended action"""
    try:
        data = request.json
        state = data.get('state', {})
        gambler = data.get('gambler', {})
        timestamp = data.get('timestamp', datetime.now().isoformat())
        strategy_name = data.get('strategy', 'basic_strategy')
        formkey = data.get('formkey', 'default')
        
        # Log the game state
        logger.info(f"Received game state: {state.get('status')} [formkey: {formkey}]")
        
        # Store in database
        hand_id = db.store_hand(state, gambler, timestamp, formkey)
        
        # Determine action if game is in progress
        action = 'none'
        
        if state.get('status') == 'PLAYING':
            # Load strategy
            strategy = load_strategy(strategy_name)
            
            # Get available actions
            available_actions = state.get('actions', [])
            
            # Parse cards
            player_cards = state.get('player', [])
            dealer_upcard = state.get('dealer', [None])[0]
            
            # Calculate values
            player_value = calculate_hand_value(player_cards)
            dealer_value = parse_card(dealer_upcard)[0] if dealer_upcard else 0
            
            # Check for split scenario
            if state.get('has_player_split'):
                # Handle split hands
                if 'HIT_SPLIT' in available_actions or 'STAY_SPLIT' in available_actions:
                    # Playing split hand
                    split_cards = state.get('player_split', [])
                    split_value = calculate_hand_value(split_cards)
                    action = strategy.get_action(
                        split_value, 
                        dealer_value, 
                        available_actions,
                        is_split=True,
                        cards=split_cards
                    )
                else:
                    # Playing main hand after split
                    action = strategy.get_action(
                        player_value, 
                        dealer_value, 
                        available_actions,
                        is_split=False,
                        cards=player_cards
                    )
            else:
                # Normal hand
                action = strategy.get_action(
                    player_value, 
                    dealer_value, 
                    available_actions,
                    is_split=False,
                    cards=player_cards
                )
            
            # Store the action
            if action != 'none':
                db.store_action(hand_id, action, player_value, dealer_value)
                logger.info(f"Recommended action: {action} (Player: {player_value}, Dealer: {dealer_value})")
        
        elif state.get('actions') and 'DEAL' in state.get('actions', []):
            # Hand is complete, ready for new deal
            action = 'none'  # Let the Tampermonkey script handle dealing
            
            # Update hand outcome in database
            db.update_hand_outcome(hand_id, state)
        
        return jsonify({
            'action': action,
            'hand_id': hand_id
        })
    
    except Exception as e:
        logger.error(f"Error handling game state: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Return current statistics"""
    try:
        formkey = request.args.get('formkey', None)
        stats = db.get_statistics(formkey)
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.info("Health check requested - Client connected successfully")
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat(), 'message': 'Flask server is running'})

def run_server():
    """Run the Flask server with HTTPS"""
    # Get configuration from environment variables
    port = int(os.getenv('PORT', 8080))
    cert_file = os.getenv('SSL_PUBLIC_CERT_PATH', 'certs/cert.pem')
    key_file = os.getenv('SSL_PRIVATE_KEY_PATH', 'certs/key.pem')
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        logger.info(f"Running with HTTPS using certificates: {cert_file}, {key_file}")
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            ssl_context=(cert_file, key_file)
        )
    else:
        logger.warning(f"No SSL certificates found at {cert_file}, {key_file}. Run generate_cert.sh first.")
        logger.info(f"Running without HTTPS (HTTP only) on port {port}")
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False
        )

if __name__ == '__main__':
    run_server()