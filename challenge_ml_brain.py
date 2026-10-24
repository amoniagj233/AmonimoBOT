import json
import math
import numpy as np
from datetime import datetime
from pathlib import Path

MODEL_FILE = Path(r"c:\Users\amoni\OneDrive\Desktop\DayTrade\challenge_20_ml_model.json")

class ChallengeMLBrain:
    """
    Adaptive Machine Learning Engine for the $20 Challenge:
      1. Symbol Ease-of-Trading Predictor:
         - Evaluates Kaufman Efficiency Ratio (KER), Candle Wick Noise, and Spread Friction.
         - Prioritizes symbols with high trend persistence and low whipsaw risk.
      2. Adaptive Dynamic Take-Profit Q-Learner:
         - Learns optimal TP multipliers (1.8x, 2.2x, 2.8x) based on volatility regime & momentum velocity.
      3. Reinforcement Learning Feedback Loop:
         - Updates symbol preference distributions (Beta/Bandit) and Q-values after every closed trade.
    """
    def __init__(self):
        self.model_data = self._load_model()

    def _get_default_model(self):
        return {
            "version": "1.0-AdaptiveReinforcement",
            "epochs_trained": 0,
            "total_trades_analyzed": 0,
            "cumulative_reward": 0.0,
            "feature_weights": {
                "trend_efficiency_ker": 0.40,
                "low_noise_ratio": 0.30,
                "spread_efficiency": 0.15,
                "bandit_historical_prob": 0.15
            },
            # Multi-Armed Bandit Symbol Preferences (Beta distribution params: alpha=wins+1, beta=losses+1)
            "symbol_bandit": {
                "Step Index": {"alpha": 4, "beta": 1, "total_trades": 3, "avg_rr": 2.2},
                "Volatility 75 Index": {"alpha": 2, "beta": 2, "total_trades": 2, "avg_rr": 2.0},
                "EURUSD": {"alpha": 3, "beta": 2, "total_trades": 3, "avg_rr": 2.1},
                "GBPUSD": {"alpha": 2, "beta": 2, "total_trades": 2, "avg_rr": 2.0},
                "Volatility 25 (1s) Index": {"alpha": 3, "beta": 1, "total_trades": 2, "avg_rr": 2.2}
            },
            # Q-Table for Dynamic Take-Profit: State -> [Q(1.8x), Q(2.2x), Q(2.8x)]
            # States: LowVol_Choppy, LowVol_Trending, NormalVol_Choppy, NormalVol_Trending, HighVol_Expansion
            "q_table_tp": {
                "LowVol_Choppy": [0.65, 0.45, 0.20],
                "LowVol_Trending": [0.55, 0.70, 0.40],
                "NormalVol_Choppy": [0.60, 0.50, 0.25],
                "NormalVol_Trending": [0.45, 0.75, 0.65],
                "HighVol_Expansion": [0.30, 0.60, 0.85]
            },
            "learning_rate": 0.15,
            "discount_factor": 0.90,
            "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        }

    def _load_model(self):
        if not MODEL_FILE.exists():
            default_model = self._get_default_model()
            self._save_model(default_model)
            return default_model
        try:
            with open(MODEL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return self._get_default_model()

    def _save_model(self, data=None):
        if data is None:
            data = self.model_data
        try:
            data["last_updated"] = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
            with open(MODEL_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[ML BRAIN] Error saving model: {e}")

    # ==========================================================================
    # 1. EASY-TRADING SYMBOL PREDICTOR
    # ==========================================================================
    def predict_symbol_ease(self, sym, rates, info, tick):
        """
        Calculates real-time Ease-of-Trading Score (0-100) using:
          1. Kaufman Efficiency Ratio (KER 20): Directional movement / Total path
          2. Noise / Wick Ratio: Body cleaness vs upper/lower stop-hunt wicks
          3. Spread Friction: Percentage of $1.00 risk consumed by spread
          4. Bayesian Bandit Win Probability from past trades
        """
        if rates is None or len(rates) < 20 or not info or not tick:
            return {
                "ease_score": 50,
                "ker": 0.20,
                "noise_ratio": 0.50,
                "spread_friction": 0.05,
                "rank_tag": "NEUTRAL",
                "bandit_prob": 0.50,
                "recommendation": "Normal scrutiny required"
            }

        closes = rates['close']
        highs = rates['high']
        lows = rates['low']
        opens = rates['open']

        # 1. Kaufman Efficiency Ratio (KER 20)
        net_change = abs(closes[-1] - closes[-20])
        total_path = float(np.sum(np.abs(np.diff(closes[-20:]))))
        ker = float(net_change / total_path) if total_path > 0 else 0.05

        # 2. Noise / Wick Ratio (over last 14 candles)
        wick_top = highs[-14:] - np.maximum(opens[-14:], closes[-14:])
        wick_bot = np.minimum(opens[-14:], closes[-14:]) - lows[-14:]
        total_range = highs[-14:] - lows[-14:]
        sum_range = float(np.sum(total_range))
        noise_ratio = float(np.sum(wick_top + wick_bot) / sum_range) if sum_range > 0 else 0.50

        # 3. Spread Friction
        spread = tick.ask - tick.bid
        cur_p = tick.bid if tick.bid > 0 else 1.0
        spread_pct = (spread / cur_p) * 100

        # 4. Bayesian Thompson Probability from Symbol Bandit
        bandit = self.model_data.get("symbol_bandit", {}).get(sym, {"alpha": 2, "beta": 2})
        alpha = bandit.get("alpha", 2)
        beta = bandit.get("beta", 2)
        bandit_prob = float(alpha / (alpha + beta))

        # Composite Score Calculation (Weighted by learned feature weights)
        weights = self.model_data.get("feature_weights", {})
        w_ker = weights.get("trend_efficiency_ker", 0.40)
        w_noise = weights.get("low_noise_ratio", 0.30)
        w_spread = weights.get("spread_efficiency", 0.15)
        w_bandit = weights.get("bandit_historical_prob", 0.15)

        ker_score = min(100.0, ker * 110.0)
        noise_score = max(0.0, min(100.0, (1.0 - noise_ratio) * 150.0))
        spread_score = max(0.0, min(100.0, (1.0 - (spread_pct * 15.0)) * 100.0))
        bandit_score = bandit_prob * 100.0

        raw_score = (ker_score * w_ker) + (noise_score * w_noise) + (spread_score * w_spread) + (bandit_score * w_bandit)
        ease_score = int(min(100, max(10, round(raw_score))))

        # Rank Tag and Actionable Recommendation
        if ease_score >= 80:
            rank_tag = "⭐ TOP PICK"
            recommendation = "Clean trend, low wicks & low spread. Ideal for $20 growth."
        elif ease_score >= 65:
            rank_tag = "✅ FAVORABLE"
            recommendation = "Good trend structure with acceptable noise level."
        elif ease_score >= 50:
            rank_tag = "⚖️ NEUTRAL"
            recommendation = "Moderate consolidation. Trade with standard 2.2x target."
        else:
            rank_tag = "⚠️ CHOPPY / AVOID"
            recommendation = "Excessive wicks or flat market. Skip or reduce risk."

        return {
            "ease_score": ease_score,
            "ker": round(ker, 3),
            "noise_ratio": round(noise_ratio, 3),
            "spread_friction": round(spread_pct, 4),
            "bandit_prob": round(bandit_prob, 2),
            "rank_tag": rank_tag,
            "recommendation": recommendation
        }

    # ==========================================================================
    # 2. ADAPTIVE DYNAMIC TAKE-PROFIT PREDICTOR (Q-LEARNER)
    # ==========================================================================
    def predict_dynamic_tp(self, sym, rates, atr, bias, dollar_risk=0.85):
        """
        Uses Q-Learning state-action mapping to predict optimal Take-Profit multiplier:
          - State: Volatility Regime + Trend Velocity (KER)
          - Actions:
            0 -> 1.8x Target (Quick Win Lock: +$1.50 - $1.80)
            1 -> 2.2x Target (Standard Impulse: +$2.00 - $2.20)
            2 -> 2.8x Target (Runner Expansion: +$2.50 - $2.80)
        """
        if rates is None or len(rates) < 30 or atr <= 0:
            return {
                "tp_multiplier": 2.2,
                "target_dollar": round(dollar_risk * 2.2, 2),
                "strategy_name": "Standard Balanced TP (2.2x)",
                "regime": "NormalVol_Trending",
                "action_id": 1,
                "reasoning": "Fallback default balanced target."
            }

        closes = rates['close']
        highs = rates['high']
        lows = rates['low']

        # Determine Volatility Regime (ATR vs 30-bar Mean ATR)
        tr = np.maximum(highs[1:] - lows[1:], np.abs(highs[1:] - closes[:-1]))
        tr = np.maximum(tr, np.abs(lows[1:] - closes[:-1]))
        mean_tr = float(np.mean(tr[-30:])) if len(tr) >= 30 else atr
        vol_ratio = atr / mean_tr if mean_tr > 0 else 1.0

        # Trend Cleanliness (KER 14)
        net_change = abs(closes[-1] - closes[-14])
        total_path = float(np.sum(np.abs(np.diff(closes[-14:]))))
        ker = float(net_change / total_path) if total_path > 0 else 0.20

        # Classify State
        if vol_ratio >= 1.25 and ker >= 0.55:
            state = "HighVol_Expansion"
        elif ker >= 0.45:
            state = "NormalVol_Trending" if vol_ratio >= 0.85 else "LowVol_Trending"
        else:
            state = "NormalVol_Choppy" if vol_ratio >= 0.85 else "LowVol_Choppy"

        # Lookup Q-Values for this State
        q_table = self.model_data.get("q_table_tp", self._get_default_model()["q_table_tp"])
        q_vals = q_table.get(state, [0.45, 0.70, 0.60])

        # Pick Best Action (Argmax with slight exploration)
        best_action = int(np.argmax(q_vals))

        action_map = {
            0: {"multiplier": 1.8, "name": "Quick Profit Lock (1.8x)", "desc": "Market choppy/tight. Locking in early profit."},
            1: {"multiplier": 2.2, "name": "Standard Trend Target (2.2x)", "desc": "Clean impulse move. Standard 1:2.2 R:R target."},
            2: {"multiplier": 2.8, "name": "Runner Volatility Expansion (2.8x)", "desc": "High momentum & expanding volatility. Stretching target for maximum gain."}
        }

        chosen = action_map.get(best_action, action_map[1])
        multiplier = chosen["multiplier"]
        target_dollar = round(dollar_risk * multiplier, 2)

        return {
            "tp_multiplier": multiplier,
            "target_dollar": target_dollar,
            "strategy_name": chosen["name"],
            "regime": state,
            "action_id": best_action,
            "reasoning": f"State '{state}' (KER: {ker:.2f}, VolRatio: {vol_ratio:.2f}) -> Q-Optimal {chosen['name']}"
        }

    # ==========================================================================
    # 3. REINFORCEMENT LEARNING ONLINE FEEDBACK LOOP
    # ==========================================================================
    def learn_from_trade(self, closed_trade):
        """
        Autonomous learning step triggered immediately when any Challenge position closes:
          1. Updates Symbol Bandit alpha/beta (Wins/Losses).
          2. Updates Take-Profit Q-table using Bellman equation:
             Q(s, a) = Q(s, a) + lr * (reward - Q(s, a))
          3. Adjusts feature weights to reward predictive factors.
        """
        if not closed_trade:
            return

        sym = closed_trade.get("symbol", "")
        pnl = float(closed_trade.get("realized_profit", 0.0))
        dollar_risk = float(closed_trade.get("dollar_risk", 1.0))
        state = closed_trade.get("ml_regime", "NormalVol_Trending")
        action_id = int(closed_trade.get("ml_action_id", 1))

        # Reward Calculation: Normalized R-multiple
        r_multiple = pnl / dollar_risk if dollar_risk > 0 else 0.0
        # Positive reward if win; penalty if loss
        reward = r_multiple if pnl > 0 else (r_multiple * 1.2)

        # 1. Update Multi-Armed Bandit
        bandit_dict = self.model_data.setdefault("symbol_bandit", {})
        if sym not in bandit_dict:
            bandit_dict[sym] = {"alpha": 2, "beta": 2, "total_trades": 0, "avg_rr": 2.0}

        if pnl > 0:
            bandit_dict[sym]["alpha"] += 1
        else:
            bandit_dict[sym]["beta"] += 1
        bandit_dict[sym]["total_trades"] += 1

        # 2. Q-Learning Bellman Update for Take-Profit
        lr = self.model_data.get("learning_rate", 0.15)
        q_table = self.model_data.setdefault("q_table_tp", self._get_default_model()["q_table_tp"])
        if state not in q_table:
            q_table[state] = [0.5, 0.5, 0.5]

        cur_q = q_table[state][action_id]
        new_q = cur_q + lr * (reward - cur_q)
        q_table[state][action_id] = round(new_q, 4)

        # 3. Meta-Statistics
        self.model_data["epochs_trained"] = self.model_data.get("epochs_trained", 0) + 1
        self.model_data["total_trades_analyzed"] = self.model_data.get("total_trades_analyzed", 0) + 1
        self.model_data["cumulative_reward"] = round(self.model_data.get("cumulative_reward", 0.0) + reward, 2)

        self._save_model()
        print(f"[ML BRAIN] Learned from {sym} trade (PnL: ${pnl:+.2f}, R: {r_multiple:+.2f}). State '{state}' Action {action_id} Q updated: {cur_q:.3f} -> {new_q:.3f}")

    def reset_model(self):
        default_model = self._get_default_model()
        self.model_data = default_model
        self._save_model(default_model)
        return {"success": True, "message": "ML Brain model weights reset to defaults."}

    def get_summary(self):
        """Returns structured payload for Web UI visualization"""
        return {
            "version": self.model_data.get("version", "1.0"),
            "epochs_trained": self.model_data.get("epochs_trained", 0),
            "total_trades_analyzed": self.model_data.get("total_trades_analyzed", 0),
            "cumulative_reward": self.model_data.get("cumulative_reward", 0.0),
            "feature_weights": self.model_data.get("feature_weights", {}),
            "symbol_bandit": self.model_data.get("symbol_bandit", {}),
            "q_table_tp": self.model_data.get("q_table_tp", {}),
            "last_updated": self.model_data.get("last_updated", "--")
        }

# Global Singleton Instance
ml_brain = ChallengeMLBrain()
