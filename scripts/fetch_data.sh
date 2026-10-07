#!/usr/bin/env bash
# Auto-fetch the source datasets for the from-scratch (GPU) reproduce path.
#
# The redistributed repository ships only the clean ESTER-Pt RIB/HYB run of
# record (CC BY 4.0, public-domain literature, no PII). The forms (XFUND),
# identity-document and English-control (FUNSD) raw inputs are NOT
# redistributed here for licence and privacy reasons; this script downloads them
# straight from their authoritative sources so the from-scratch path needs no
# manual data placement -- as if the data were already there.
#
# The no-GPU reviewer path does NOT need this script: it reproduces every paper
# number from the committed run of record offline (see README "Minimal test").
#
# Properties:
#   - Idempotent: a dataset already present (and, where a checksum is known,
#     verified) is skipped on re-runs.
#   - Checksum-verified: each download is sha256-checked against scripts/data.sha256
#     when an entry exists there; mismatches abort. Unknown checksums are recorded
#     for first-run pinning and warned about, never silently trusted.
#   - Identity documents: the scored set is the CNH/RG part of the ``valid`` split
#     of tech4humans/br-doc-extraction (Hugging Face; images from the BID Dataset).
#     See the Erratum in README.md.
#
# Each dataset's source is downloaded under its own licence (see data/DATA-LICENSES.md):
#   XFUND  CC BY-NC-SA 4.0   FUNSD  research-only   ESTER-Pt  CC BY 4.0
#   identity documents (tech4humans/br-doc-extraction, from BID)  licence unstated
#
# Usage:
#   ./scripts/fetch_data.sh [all|xfund|funsd|ester|ids]   (default: all)
# Configuration:
#   WORK_DIR  destination root (default: $PWD/data); per-axis subdirs are created.
set -euo pipefail
cd "$(dirname "$0")/.."

WORK_DIR="${WORK_DIR:-$PWD/data}"
SUMS_FILE="$PWD/scripts/data.sha256"
WHAT="${1:-all}"

c_red=$'\033[31m'; c_grn=$'\033[32m'; c_yel=$'\033[33m'; c_off=$'\033[0m'
info() { printf '%s[fetch]%s %s\n' "$c_grn" "$c_off" "$*"; }
warn() { printf '%s[warn]%s  %s\n' "$c_yel" "$c_off" "$*" >&2; }
die()  { printf '%s[fail]%s  %s\n' "$c_red" "$c_off" "$*" >&2; exit 1; }

command -v curl >/dev/null || die "curl is required"
command -v unzip >/dev/null || warn "unzip not found; zip archives will be left unextracted"
SHA=""
command -v sha256sum >/dev/null && SHA="sha256sum"
[ -z "$SHA" ] && command -v shasum >/dev/null && SHA="shasum -a 256"

# sha256 of a file (empty string if no tool available).
sum_of() { [ -n "$SHA" ] && $SHA "$1" | awk '{print $1}' || echo ""; }

# Verify $1 against the pinned checksum in scripts/data.sha256 keyed by basename.
# Returns 0 if it matches a pin, 1 if it mismatches (caller aborts), 2 if no pin.
verify_sum() {
  local f="$1" base want got
  base="$(basename "$f")"
  [ -f "$SUMS_FILE" ] || return 2
  want="$(awk -v b="$base" '$2==b || $2=="*"b {print $1; exit}' "$SUMS_FILE" 2>/dev/null || true)"
  [ -n "$want" ] || return 2
  got="$(sum_of "$f")"
  [ -z "$got" ] && { warn "no sha256 tool; cannot verify $base"; return 2; }
  [ "$got" = "$want" ] && return 0 || { warn "sha256 mismatch for $base"; return 1; }
}

# Download $url to $dest unless a verified copy already exists (idempotent).
fetch() {
  local url="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  if [ -f "$dest" ]; then
    if verify_sum "$dest"; then info "have (verified): $(basename "$dest")"; return 0; fi
    case $? in
      1) die "existing $(basename "$dest") fails its pinned checksum; delete it and re-run" ;;
      2) info "have (unpinned): $(basename "$dest"), sha256=$(sum_of "$dest")"; return 0 ;;
    esac
  fi
  info "downloading $(basename "$dest") <- $url"
  curl -fSL --retry 3 --retry-delay 2 -o "$dest.part" "$url" || die "download failed: $url"
  mv "$dest.part" "$dest"
  if verify_sum "$dest"; then info "verified: $(basename "$dest")"
  elif [ $? -eq 1 ]; then die "downloaded $(basename "$dest") fails its pinned checksum"
  else warn "no pinned checksum for $(basename "$dest"); record this to pin it:"; echo "  $(sum_of "$dest")  $(basename "$dest")"; fi
}

extract_zip() {
  local zip="$1" into="$2"
  command -v unzip >/dev/null || { warn "skip extract (no unzip): $zip"; return 0; }
  mkdir -p "$into"; unzip -n -q "$zip" -d "$into" && info "extracted -> $into"
}

# --- XFUND, Portuguese split (forms axis). Source: official GitHub release v1.0.
#     All four asset URLs verified HTTP 200 on 2026-06-22. Licence CC BY-NC-SA 4.0.
fetch_xfund() {
  info "XFUND PT split (forms axis) -- CC BY-NC-SA 4.0"
  local base="https://github.com/doc-analysis/XFUND/releases/download/v1.0"
  local out="$WORK_DIR/forms/_source/xfund"
  fetch "$base/pt.train.json" "$out/pt.train.json"
  fetch "$base/pt.train.zip"  "$out/pt.train.zip"
  fetch "$base/pt.val.json"   "$out/pt.val.json"
  fetch "$base/pt.val.zip"    "$out/pt.val.zip"
  extract_zip "$out/pt.train.zip" "$out/pt.train"
  extract_zip "$out/pt.val.zip"   "$out/pt.val"
  info "XFUND PT ready under $out (the paper scores the pt.val images)"
}

# --- FUNSD (English-control axis). Source: official project page.
#     URL verified HTTP 200 (16.8 MB) on 2026-06-22. Research-only licence.
fetch_funsd() {
  info "FUNSD (English control axis) -- research-only"
  local out="$WORK_DIR/en/_source/funsd"
  fetch "https://guillaumejaume.github.io/FUNSD/dataset.zip" "$out/dataset.zip"
  extract_zip "$out/dataset.zip" "$out"
  info "FUNSD ready under $out"
}

# --- ESTER-Pt (RIB/HYB axes). Source: Zenodo record 7872951.
#     Record + file URL verified HTTP 200 on 2026-06-22. Licence CC BY 4.0.
#     NOTE: the single archive is ~19.6 GB; the clean RIB/HYB gold + run of record
#     is already committed, so the reviewer never needs this download.
fetch_ester() {
  info "ESTER-Pt RIB/HYB images -- CC BY 4.0 (~19.6 GB; only the from-scratch path needs it)"
  local out="$WORK_DIR/_source/ester-pt"
  fetch "https://zenodo.org/api/records/7872951/files/ESTER-Pt.zip/content" "$out/ESTER-Pt.zip"
  extract_zip "$out/ESTER-Pt.zip" "$out"
  info "ESTER-Pt ready under $out"
}

# --- Identity documents (ids axis). Source: Hugging Face dataset
#     tech4humans/br-doc-extraction, ``valid`` split: 25 CNH + 25 RG + 25 invoices;
#     the invoices are skipped. Its images were sampled from the BID Dataset
#     (Soares et al., SIBGRAPI 2020). Licence unstated on both. URL verified HTTP 200
#     on 2026-10-07; the regenerated gold yields the paper's 354 scored fields.
#     See the Erratum in README.md.
fetch_ids() {
  info "identity documents (ids axis) -- tech4humans/br-doc-extraction valid split"
  local out="$WORK_DIR/ids"
  local pq="$out/_source/br-doc-extraction/valid-00000-of-00001.parquet"
  fetch "https://huggingface.co/datasets/tech4humans/br-doc-extraction/resolve/main/data/valid-00000-of-00001.parquet" "$pq"
  if python3 scripts/ids_from_parquet.py "$pq" "$out"; then
    info "identity axis ready under $out (25 CNH + 25 RG, invoices skipped)"
  else
    warn "could not materialize the identity axis (pyarrow missing?); see scripts/ids_from_parquet.py"
  fi
}

case "$WHAT" in
  all)   fetch_xfund; fetch_funsd; fetch_ester; fetch_ids ;;
  xfund) fetch_xfund ;;
  funsd) fetch_funsd ;;
  ester) fetch_ester ;;
  ids)   fetch_ids ;;
  bridp) warn "'bridp' is now 'ids' (see the Erratum in README.md)"; fetch_ids ;;
  *) die "unknown target '$WHAT' (use: all|xfund|funsd|ester|ids)" ;;
esac

info "done. From-scratch generation: run engines over the fetched images, then"
info "score with ./scripts/reproduce_from_results.sh (see docs/PROTOCOL.md)."
