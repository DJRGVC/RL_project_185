synthetic rows: 14  real rows: 80

## Aggregated mean ± SEM per (source, model, variant)

| source | model | variant | plaus | goal_prog | spec | conf | n |
| --- | --- | --- | :-: | :-: | :-: | :-: | :-: |
| real | `claude-opus-4-7` | `achieved_goal` | 0.47±0.09 (n=6) | 0.97±0.03 (n=6) | 0.50±0.07 (n=6) | 0.52±0.09 (n=10) | 10 |
| real | `claude-opus-4-7` | `action` | 0.51±0.09 (n=7) | 0.39±0.11 (n=7) | 0.67±0.05 (n=7) | 0.59±0.01 (n=10) | 10 |
| real | `claude-opus-4-7` | `all` | 0.67±0.06 (n=8) | 0.56±0.09 (n=8) | 0.79±0.02 (n=8) | 0.64±0.02 (n=10) | 10 |
| real | `claude-opus-4-7` | `narrative` | 0.86±0.01 (n=8) | 0.69±0.04 (n=8) | 0.49±0.02 (n=8) | 0.69±0.08 (n=10) | 10 |
| real | `claude-sonnet-4-5` | `achieved_goal` | 0.81±0.07 (n=9) | 0.89±0.02 (n=9) | 0.69±0.04 (n=9) | 0.85±0.00 (n=10) | 10 |
| real | `claude-sonnet-4-5` | `action` | 0.47±0.05 (n=8) | 0.19±0.01 (n=8) | 0.64±0.03 (n=8) | 0.84±0.00 (n=10) | 10 |
| real | `claude-sonnet-4-5` | `all` | 0.68±0.07 (n=8) | 0.47±0.10 (n=8) | 0.73±0.04 (n=8) | 0.89±0.01 (n=10) | 10 |
| real | `claude-sonnet-4-5` | `narrative` | 0.84±0.03 (n=7) | 0.64±0.02 (n=7) | 0.43±0.02 (n=7) | 0.92±0.01 (n=10) | 10 |
| synthetic | `claude-opus-4-7` | `achieved_goal` | 0.46±0.18 (n=4) | 0.97±0.01 (n=4) | 0.49±0.13 (n=4) | 0.68±0.02 (n=4) | 4 |
| synthetic | `claude-opus-4-7` | `action` | 0.55±0.09 (n=4) | 0.53±0.16 (n=4) | 0.65±0.05 (n=4) | 0.43±0.02 (n=4) | 4 |
| synthetic | `claude-opus-4-7` | `all` | 0.70±0.10 (n=2) | 0.62±0.12 (n=2) | 0.82±0.02 (n=2) | 0.70±0.10 (n=2) | 2 |
| synthetic | `claude-opus-4-7` | `narrative` | 0.79±0.04 (n=4) | 0.68±0.06 (n=4) | 0.40±0.04 (n=4) | 0.82±0.01 (n=4) | 4 |

## Teleport-collapse rates (||cf_pos − dg|| < 5cm)

| source | model | env | variant | teleport_rate | n |
| --- | --- | --- | --- | :-: | :-: |
| real | `claude-opus-4-7` | FetchPickAndPlace-v4 | `achieved_goal` | 0.75 (3/4) | 6 |
| real | `claude-opus-4-7` | FetchPickAndPlace-v4 | `all` | 0.17 (1/6) | 6 |
| real | `claude-opus-4-7` | FetchPush-v4 | `achieved_goal` | 1.00 (4/4) | 4 |
| real | `claude-opus-4-7` | FetchPush-v4 | `all` | 0.25 (1/4) | 4 |
| real | `claude-sonnet-4-5` | FetchPickAndPlace-v4 | `achieved_goal` | 0.00 (0/6) | 6 |
| real | `claude-sonnet-4-5` | FetchPickAndPlace-v4 | `all` | 0.17 (1/6) | 6 |
| real | `claude-sonnet-4-5` | FetchPush-v4 | `achieved_goal` | 0.75 (3/4) | 4 |
| real | `claude-sonnet-4-5` | FetchPush-v4 | `all` | 0.50 (2/4) | 4 |
| synthetic | `claude-opus-4-7` | FetchPickAndPlace-v4 | `achieved_goal` | 1.00 (2/2) | 2 |
| synthetic | `claude-opus-4-7` | FetchPickAndPlace-v4 | `all` | 1.00 (1/1) | 1 |
| synthetic | `claude-opus-4-7` | FetchPush-v4 | `achieved_goal` | 1.00 (2/2) | 2 |
| synthetic | `claude-opus-4-7` | FetchPush-v4 | `all` | 1.00 (1/1) | 1 |

## Synthetic-vs-real comparison (Opus 4.7 only)

| variant | metric | C1 synthetic | C1v2 real | Δ (real-synth) |
| --- | --- | :-: | :-: | :-: |
| `narrative` | plausibility | 0.79±0.04 (n=4) | 0.86±0.01 (n=8) | +0.07 |
| `narrative` | specificity | 0.40±0.04 (n=4) | 0.49±0.02 (n=8) | +0.09 |
| `action` | plausibility | 0.55±0.09 (n=4) | 0.51±0.09 (n=7) | -0.04 |
| `action` | specificity | 0.65±0.05 (n=4) | 0.67±0.05 (n=7) | +0.02 |
| `achieved_goal` | plausibility | 0.46±0.18 (n=4) | 0.47±0.09 (n=6) | +0.00 |
| `achieved_goal` | specificity | 0.49±0.13 (n=4) | 0.50±0.07 (n=6) | +0.01 |
| `all` | plausibility | 0.70±0.10 (n=2) | 0.67±0.06 (n=8) | -0.03 |
| `all` | specificity | 0.82±0.02 (n=2) | 0.79±0.02 (n=8) | -0.04 |

## F2 — `action` axis sign-flip rates

Rate of action-axes whose sign disagrees with sign(desired_goal - achieved_goal_at_failure), per (source, model, variant). Only counts axes with goal_dir > 1 cm and |action_i| > 0.05.

| source | model | variant | sign-flip rate | n |
| --- | --- | --- | :-: | :-: |
| real | `claude-opus-4-7` | `action` | 0.55 | 10 |
| real | `claude-opus-4-7` | `all` | 0.39 | 9 |
| real | `claude-sonnet-4-5` | `action` | 0.70 | 5 |
| real | `claude-sonnet-4-5` | `all` | 0.50 | 6 |
| synthetic | `claude-opus-4-7` | `action` | 0.50 | 4 |
| synthetic | `claude-opus-4-7` | `all` | 0.17 | 2 |

## F5 — VLM confidence vs judge plausibility (Spearman)

- synthetic: ρ = +0.45 (p = 0.103, n = 14)
- real: ρ = +0.27 (p = 0.034, n = 61)

## All real-data achieved_goal + all variants — teleport check

| env | seed | model | variant | dg | cf_pos | dist_to_dg | plaus |
| --- | --- | --- | --- | --- | --- | :-: | :-: |
| PickAndPlace-v | 50000 | `claude-opus-4-7` | `achieved_goal` | [1.36, 0.88, 0.42] | [1.36, 0.88, 0.42] | 0.000 TELEPORT | 0.50 |
| PickAndPlace-v | 50000 | `claude-opus-4-7` | `all` | [1.36, 0.88, 0.42] | [1.30, 0.75, 0.43] | 0.143  | 0.85 |
| PickAndPlace-v | 50000 | `claude-sonnet-4-5` | `achieved_goal` | [1.36, 0.88, 0.42] | [1.36, 0.88, 0.50] | 0.075  | 0.90 |
| PickAndPlace-v | 50000 | `claude-sonnet-4-5` | `all` | [1.36, 0.88, 0.42] | [1.36, 0.88, 0.50] | 0.075  | 0.85 |
| PickAndPlace-v | 50034 | `claude-opus-4-7` | `achieved_goal` | [1.41, 0.75, 0.42] | [1.41, 0.75, 0.50] | 0.075  | 0.90 |
| PickAndPlace-v | 50034 | `claude-opus-4-7` | `all` | [1.41, 0.75, 0.42] | [1.30, 0.75, 0.43] | 0.109  | 0.75 |
| PickAndPlace-v | 50034 | `claude-sonnet-4-5` | `achieved_goal` | [1.41, 0.75, 0.42] | [1.41, 0.74, 0.50] | 0.075  | 0.90 |
| PickAndPlace-v | 50034 | `claude-sonnet-4-5` | `all` | [1.41, 0.75, 0.42] | [1.34, 0.75, 0.50] | 0.102  | 0.85 |
| PickAndPlace-v | 50051 | `claude-opus-4-7` | `achieved_goal` | [1.26, 0.82, 0.63] | [1.26, 0.82, 0.63] | 0.000 TELEPORT | — |
| PickAndPlace-v | 50051 | `claude-opus-4-7` | `all` | [1.26, 0.82, 0.63] | [1.20, 0.75, 0.45] | 0.202  | — |
| PickAndPlace-v | 50051 | `claude-sonnet-4-5` | `achieved_goal` | [1.26, 0.82, 0.63] | [1.26, 0.82, 0.50] | 0.129  | 0.90 |
| PickAndPlace-v | 50051 | `claude-sonnet-4-5` | `all` | [1.26, 0.82, 0.63] | [1.26, 0.82, 0.63] | 0.000 TELEPORT | 0.40 |
| PickAndPlace-v | 50068 | `claude-opus-4-7` | `all` | [1.43, 0.73, 0.42] | [1.38, 0.70, 0.43] | 0.057  | 0.85 |
| PickAndPlace-v | 50068 | `claude-sonnet-4-5` | `achieved_goal` | [1.43, 0.73, 0.42] | [1.36, 0.73, 0.55] | 0.141  | 0.85 |
| PickAndPlace-v | 50068 | `claude-sonnet-4-5` | `all` | [1.43, 0.73, 0.42] | [1.34, 0.73, 0.50] | 0.114  | — |
| PickAndPlace-v | 50085 | `claude-opus-4-7` | `all` | [1.34, 0.89, 0.55] | [1.34, 0.89, 0.55] | 0.000 TELEPORT | 0.45 |
| PickAndPlace-v | 50085 | `claude-sonnet-4-5` | `achieved_goal` | [1.34, 0.89, 0.55] | [1.34, 0.88, 0.65] | 0.104  | 0.70 |
| PickAndPlace-v | 50085 | `claude-sonnet-4-5` | `all` | [1.34, 0.89, 0.55] | [1.34, 0.75, 0.43] | 0.178  | 0.75 |
| PickAndPlace-v | 50102 | `claude-opus-4-7` | `achieved_goal` | [1.44, 0.84, 0.42] | [1.44, 0.84, 0.42] | 0.000 TELEPORT | 0.40 |
| PickAndPlace-v | 50102 | `claude-opus-4-7` | `all` | [1.44, 0.84, 0.42] | [1.30, 0.75, 0.43] | 0.172  | 0.60 |
| PickAndPlace-v | 50102 | `claude-sonnet-4-5` | `achieved_goal` | [1.44, 0.84, 0.42] | [1.45, 0.84, 0.50] | 0.075  | 0.90 |
| PickAndPlace-v | 50102 | `claude-sonnet-4-5` | `all` | [1.44, 0.84, 0.42] | [1.34, 0.75, 0.50] | 0.158  | 0.50 |
| Push-v4 | 60000 | `claude-opus-4-7` | `achieved_goal` | [1.32, 0.72, 0.42] | [1.32, 0.72, 0.42] | 0.000 TELEPORT | 0.30 |
| Push-v4 | 60000 | `claude-opus-4-7` | `all` | [1.32, 0.72, 0.42] | [1.32, 0.72, 0.45] | 0.025 TELEPORT | — |
| Push-v4 | 60000 | `claude-sonnet-4-5` | `achieved_goal` | [1.32, 0.72, 0.42] | [1.29, 0.72, 0.42] | 0.026 TELEPORT | — |
| Push-v4 | 60000 | `claude-sonnet-4-5` | `all` | [1.32, 0.72, 0.42] | [1.28, 0.72, 0.42] | 0.036 TELEPORT | 0.85 |
| Push-v4 | 60017 | `claude-opus-4-7` | `achieved_goal` | [1.46, 0.62, 0.42] | [1.46, 0.62, 0.42] | 0.000 TELEPORT | 0.30 |
| Push-v4 | 60017 | `claude-opus-4-7` | `all` | [1.46, 0.62, 0.42] | [1.40, 0.62, 0.42] | 0.061  | 0.85 |
| Push-v4 | 60017 | `claude-sonnet-4-5` | `achieved_goal` | [1.46, 0.62, 0.42] | [1.42, 0.65, 0.42] | 0.050  | 0.90 |
| Push-v4 | 60017 | `claude-sonnet-4-5` | `all` | [1.46, 0.62, 0.42] | [1.42, 0.65, 0.42] | 0.050  | — |
| Push-v4 | 60034 | `claude-opus-4-7` | `achieved_goal` | [1.33, 0.88, 0.42] | [1.33, 0.88, 0.42] | 0.000 TELEPORT | — |
| Push-v4 | 60034 | `claude-opus-4-7` | `all` | [1.33, 0.88, 0.42] | [1.30, 0.75, 0.42] | 0.133  | 0.50 |
| Push-v4 | 60034 | `claude-sonnet-4-5` | `achieved_goal` | [1.33, 0.88, 0.42] | [1.33, 0.88, 0.42] | 0.000 TELEPORT | 0.30 |
| Push-v4 | 60034 | `claude-sonnet-4-5` | `all` | [1.33, 0.88, 0.42] | [1.33, 0.88, 0.42] | 0.000 TELEPORT | 0.40 |
| Push-v4 | 60051 | `claude-opus-4-7` | `achieved_goal` | [1.32, 0.78, 0.42] | [1.32, 0.78, 0.42] | 0.000 TELEPORT | 0.40 |
| Push-v4 | 60051 | `claude-opus-4-7` | `all` | [1.32, 0.78, 0.42] | [1.32, 0.72, 0.42] | 0.058  | 0.50 |
| Push-v4 | 60051 | `claude-sonnet-4-5` | `achieved_goal` | [1.32, 0.78, 0.42] | [1.29, 0.75, 0.42] | 0.039 TELEPORT | 0.95 |
| Push-v4 | 60051 | `claude-sonnet-4-5` | `all` | [1.32, 0.78, 0.42] | [1.28, 0.72, 0.42] | 0.069  | 0.85 |
