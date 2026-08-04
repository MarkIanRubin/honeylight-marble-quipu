
// ═══ deterministic test suite ═══
function run(seconds, label) {
  const steps = Math.round(seconds * 60);
  let minSupply = 999, maxSupply = 0, maxDiff = 0;
  for (let s = 0; s < steps; s++) {
    step(1/60);
    const tot = totalBalls();
    minSupply = Math.min(minSupply, tot); maxSupply = Math.max(maxSupply, tot);
    const { pe, ke } = currentTotals();
    const stored = pe + ke;
    const harvested = noteCount * HARVEST_J;
    const diff = Math.abs(energyIn - (energyOut + stored + harvested));
    maxDiff = Math.max(maxDiff, diff);
  }
  return { label, supply: `${minSupply}-${maxSupply}`, notes: noteCount,
           diff: maxDiff.toFixed(6), money: money.toFixed(2), flowers };
}

resetSong();
const r1 = run(16, "Vivaldi Spring first half");
for (const l of [0,2,4,6,8,9]) { requestDrop(l, true); }
const r2 = run(18, "through song end + burst");
gate = 'bypass';
const r3 = run(8, "bypass gravity return");
gate = 'play';
const r4 = run(6, "back to play");

console.log(JSON.stringify({
  song_events: SONG.events.length,
  song_totalMs: SONG.totalMs,
  lanes_used: [...new Set(SONG.events.map(e=>e[0]))].sort((a,b)=>a-b),
  r1, r2, r3, r4,
  PE_PER_DROP: PE_PER_DROP.toFixed(4),
  supply_now: totalBalls(),
  census_total: ballCensus().reduce((s,c)=>s+c,0),
}, null, 1));
