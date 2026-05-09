import itertools
from engine.mixing_models import get_model
from engine.simplex_projection import project_to_simplex


class WaxCalculator:
    def __init__(self, property_configs):
        self._configs = property_configs

    def _get_prop_keys(self):
        return list(self._configs.keys())

    def predict(self, materials, ratios):
        """Predict blend properties given materials and their ratios (in %)."""
        weights = [r / 100.0 for r in ratios]
        result = {}
        for key, cfg in self._configs.items():
            values = [m.get(key) for m in materials]
            if any(v is None for v in values):
                result[key] = None
                continue
            model = get_model(cfg["mixing_model"])
            result[key] = round(model.mix(values, weights), 4)
        return result

    def calculate_ratios(self, materials, targets, locked_ratios=None):
        """Calculate optimal ratios to meet target property values.

        N=2: analytical solution using most-discriminating property.
        N>=3: projected gradient descent minimizing weighted squared relative error.
        locked_ratios: {index: fixed_value_in_percent} for constraining some materials.
        """
        locked = locked_ratios or {}
        n = len(materials)
        prop_keys = [k for k in self._configs if k in targets]
        if not prop_keys:
            return None

        # Filter to properties where all materials have values
        valid_keys = []
        for k in prop_keys:
            if all(m.get(k) is not None for m in materials):
                valid_keys.append(k)
        if not valid_keys:
            return None

        locked_sum = sum(locked.values())
        free_indices = [i for i in range(n) if i not in locked]
        free_count = len(free_indices)
        if free_count == 0:
            return None

        remaining = 100.0 - locked_sum
        if remaining < 0:
            return None

        # For 2 free materials, use analytical shortcut
        if free_count == 2 and len(valid_keys) >= 1:
            return self._solve_two_free(materials, valid_keys, targets, locked, free_indices, remaining)

        # For 1 free material, trivial
        if free_count == 1:
            i = free_indices[0]
            ratios = [0.0] * n
            for j, r in locked.items():
                ratios[j] = r
            ratios[i] = remaining
            predicted = self.predict(materials, ratios)
            total_error = self._calc_error(predicted, targets, valid_keys)
            return {"ratios": [round(r, 4) for r in ratios], "predicted": predicted, "total_error": round(total_error, 6)}

        # N >= 3 free materials: projected gradient descent
        return self._gradient_descent(materials, valid_keys, targets, locked, n, remaining)

    def _solve_two_free(self, materials, valid_keys, targets, locked, free_indices, remaining):
        n = len(materials)
        i, j = free_indices

        # Find most discriminating property (largest absolute difference)
        best_key = None
        best_diff = -1
        for k in valid_keys:
            vi = materials[i].get(k)
            vj = materials[j].get(k)
            if vi is not None and vj is not None:
                diff = abs(vi - vj)
                if diff > best_diff:
                    best_diff = diff
                    best_key = k

        if best_key is None:
            return None

        target = targets[best_key]
        cfg = self._configs[best_key]
        model_name = cfg["mixing_model"]

        if model_name == "linear":
            vi = materials[i][best_key]
            vj = materials[j][best_key]
            if abs(vi - vj) < 1e-10:
                return None
            # target = (wi * vi + wj * vj) / (wi + wj), wi + wj = remaining
            # target * remaining = wi * vi + (remaining - wi) * vj
            # target * remaining = wi * vi + remaining * vj - wi * vj
            # target * remaining - remaining * vj = wi * (vi - vj)
            # wi = remaining * (target - vj) / (vi - vj)
            wi = remaining * (target - vj) / (vi - vj)
            wj = remaining - wi
        else:
            import math
            vi = max(materials[i][best_key], 1e-10)
            vj = max(materials[j][best_key], 1e-10)
            if abs(math.log(vi) - math.log(vj)) < 1e-10:
                return None
            # ln(target) = (wi * ln(vi) + wj * ln(vj)) / (wi + wj)
            # ln(target) * remaining = wi * ln(vi) + (remaining - wi) * ln(vj)
            # wi = remaining * (ln(target) - ln(vj)) / (ln(vi) - ln(vj))
            wi = remaining * (math.log(max(target, 1e-10)) - math.log(vj)) / (math.log(vi) - math.log(vj))
            wj = remaining - wi

        # Clamp
        wi = max(0, min(remaining, wi))
        wj = remaining - wi

        ratios = [0.0] * n
        for idx, r in locked.items():
            ratios[idx] = r
        ratios[i] = wi
        ratios[j] = wj

        predicted = self.predict(materials, ratios)
        total_error = self._calc_error(predicted, targets, valid_keys)
        return {"ratios": [round(r, 4) for r in ratios], "predicted": predicted, "total_error": round(total_error, 6)}

    def _gradient_descent(self, materials, valid_keys, targets, locked, n, remaining):
        free_indices = [idx for idx in range(n) if idx not in locked]
        m = len(free_indices)

        # Initialize: uniform on remaining, normalized to [0,1] simplex
        w = [1.0 / m] * m
        lr = 0.02
        best_w = w[:]
        best_error = float("inf")

        # Scale targets and properties for numerical stability
        key_scales = {}
        for k in valid_keys:
            vals = [materials[i].get(k) for i in free_indices if materials[i].get(k) is not None]
            if vals:
                key_scales[k] = max(abs(v) for v in vals) or 1.0
            else:
                key_scales[k] = 1.0

        for iteration in range(3000):
            # Compute full ratios
            ratios = [0.0] * n
            for idx, r in locked.items():
                ratios[idx] = r / 100.0
            for fi, idx in enumerate(free_indices):
                ratios[idx] = w[fi] * remaining / 100.0

            # Predict
            predicted = self.predict(materials, [r * 100 for r in ratios])

            # Compute error (scaled)
            error = 0.0
            for k in valid_keys:
                pred = predicted.get(k)
                tgt = targets[k]
                if pred is not None and pred != 0:
                    scale = key_scales[k]
                    error += ((pred - tgt) / scale) ** 2

            if error < best_error:
                best_error = error
                best_w = w[:]

            if error < 1e-12:
                break

            # Finite-difference gradient
            grad = [0.0] * m
            eps = 1e-6
            for fi in range(m):
                w_plus = w[:]
                w_plus[fi] += eps
                # Project
                w_plus = project_to_simplex(w_plus)

                r_plus = [0.0] * n
                for idx, r in locked.items():
                    r_plus[idx] = r / 100.0
                for fj, idx in enumerate(free_indices):
                    r_plus[idx] = w_plus[fj] * remaining / 100.0

                pred_plus = self.predict(materials, [rp * 100 for rp in r_plus])
                err_plus = 0.0
                for k in valid_keys:
                    p = pred_plus.get(k)
                    t = targets[k]
                    if p is not None and p != 0:
                        err_plus += ((p - t) / key_scales[k]) ** 2

                grad[fi] = (err_plus - error) / eps

            # Update with backtracking
            w_new = [w[fi] - lr * grad[fi] for fi in range(m)]
            w_new = project_to_simplex(w_new)

            # Evaluate new error
            r_new = [0.0] * n
            for idx, r in locked.items():
                r_new[idx] = r / 100.0
            for fi, idx in enumerate(free_indices):
                r_new[idx] = w_new[fi] * remaining / 100.0
            pred_new = self.predict(materials, [rp * 100 for rp in r_new])
            err_new = 0.0
            for k in valid_keys:
                p = pred_new.get(k)
                t = targets[k]
                if p is not None and p != 0:
                    err_new += ((p - t) / key_scales[k]) ** 2

            if err_new < error:
                w = w_new
            else:
                lr *= 0.5

            if max(abs(w[i] - w_new[i]) for i in range(m)) < 1e-8:
                break

        # Use best found
        ratios = [0.0] * n
        for idx, r in locked.items():
            ratios[idx] = r
        for fi, idx in enumerate(free_indices):
            ratios[idx] = best_w[fi] * remaining

        predicted = self.predict(materials, ratios)
        total_error = self._calc_error(predicted, targets, valid_keys)
        return {"ratios": [round(r, 4) for r in ratios], "predicted": predicted, "total_error": round(total_error, 6)}

    def _calc_error(self, predicted, targets, valid_keys):
        err = 0.0
        for k in valid_keys:
            p = predicted.get(k)
            t = targets[k]
            if p is not None and t != 0:
                err += ((p - t) / t) ** 2
        return err

    def optimize(self, materials, target_ranges, cost_weight=0.3, max_components=4):
        """Find top 3 best formulas given target ranges. Score = range compliance - cost penalty."""
        n = len(materials)
        max_k = min(max_components, n)

        # Use midpoints as targets for each combo
        mid_targets = {}
        prop_keys = []
        for k in target_ranges:
            rng = target_ranges[k]
            if isinstance(rng, (list, tuple)) and len(rng) == 2:
                mid_targets[k] = (rng[0] + rng[1]) / 2.0
                prop_keys.append(k)
            elif isinstance(rng, (int, float)):
                mid_targets[k] = rng
                prop_keys.append(k)

        all_results = []
        for k in range(2, max_k + 1):
            for indices in itertools.combinations(range(n), k):
                subset = [materials[i] for i in indices]
                result = self.calculate_ratios(subset, mid_targets)
                if result is None:
                    continue

                # Score: how well within ranges
                score = 0.0
                predicted = result["predicted"]
                for pk in prop_keys:
                    rng = target_ranges[pk]
                    if isinstance(rng, (list, tuple)) and len(rng) == 2:
                        lo, hi = rng
                        pval = predicted.get(pk)
                        if pval is not None:
                            if lo <= pval <= hi:
                                score += 1.0
                            elif pval < lo:
                                score += 1.0 - (lo - pval) / (lo) * 0.5 if lo != 0 else 0
                            else:
                                score += 1.0 - (pval - hi) / (hi) * 0.5 if hi != 0 else 0

                score /= len(prop_keys) if prop_keys else 1

                # Cost penalty
                ratios = result["ratios"]
                total_cost = sum(r * subset[i]["cost_per_kg"] / 100 for i, r in enumerate(ratios) if subset[i].get("cost_per_kg"))
                if cost_weight > 0:
                    all_costs = [m.get("cost_per_kg") or 0 for m in materials]
                    max_cost = max(all_costs) if all_costs else 1
                    score -= cost_weight * (total_cost / max_cost)

                all_results.append({
                    "material_ids": [subset[i]["id"] for i in range(len(subset))],
                    "material_names": [subset[i]["name"] for i in range(len(subset))],
                    "ratios": ratios,
                    "predicted": predicted,
                    "total_cost": round(total_cost, 4),
                    "score": round(score, 6),
                })

        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:3]
