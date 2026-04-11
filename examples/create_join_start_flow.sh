#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

create_resp=$(curl -sS -X POST "$BASE_URL/matches" -H 'content-type: application/json' -d '{"ruleset_name":"standard","allow_draw":true,"tick_ms":100}')
match_id=$(python - <<'PY' "$create_resp"
import json,sys
print(json.loads(sys.argv[1])["match_id"])
PY
)

echo "match_id=$match_id"

join1=$(curl -sS -X POST "$BASE_URL/matches/$match_id/join" -H 'content-type: application/json' -d '{"player_name":"red"}')
join2=$(curl -sS -X POST "$BASE_URL/matches/$match_id/join" -H 'content-type: application/json' -d '{"player_name":"black"}')

p1=$(python - <<'PY' "$join1"
import json,sys
print(json.loads(sys.argv[1])["player"]["player_id"])
PY
)
p2=$(python - <<'PY' "$join2"
import json,sys
print(json.loads(sys.argv[1])["player"]["player_id"])
PY
)

echo "p1=$p1"
echo "p2=$p2"

curl -sS -X POST "$BASE_URL/matches/$match_id/ready" -H 'content-type: application/json' -d "{\"player_id\":\"$p1\"}" >/dev/null
curl -sS -X POST "$BASE_URL/matches/$match_id/ready" -H 'content-type: application/json' -d "{\"player_id\":\"$p2\"}" >/dev/null
curl -sS -X POST "$BASE_URL/matches/$match_id/start" >/dev/null

state=$(curl -sS "$BASE_URL/matches/$match_id/state?player_id=$p1")
echo "$state" | python -m json.tool | sed -n '1,80p'

# sample move command
first_piece=$(python - <<'PY' "$state"
import json,sys
data=json.loads(sys.argv[1])
for p in data["pieces"]:
    if p["owner"] == 1 and p["kind"] == "soldier":
        print(p["id"], p["x"], p["y"]-1)
        break
PY
)
piece_id=$(echo "$first_piece" | awk '{print $1}')
tx=$(echo "$first_piece" | awk '{print $2}')
ty=$(echo "$first_piece" | awk '{print $3}')

curl -sS -X POST "$BASE_URL/matches/$match_id/commands/move" \
  -H 'content-type: application/json' \
  -d "{\"player_id\":\"$p1\",\"piece_id\":\"$piece_id\",\"target_x\":$tx,\"target_y\":$ty}" \
  | python -m json.tool | sed -n '1,80p'
