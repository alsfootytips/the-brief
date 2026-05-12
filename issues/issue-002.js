window.theBrief = window.theBrief || { issues: [] };

window.theBrief.issues.push({
  number: 2,
  date: 'Week of May 12, 2026',
  thesis: `Three different stories are converging into one: the AI infrastructure boom is being stress-tested, the Iran war just got harder to end, and quietly — without the headlines — capital has been rotating away from mega-cap tech into the rest of the market.`,

  lede: `
    <p class="lede drop-cap">Markets don't reward people who watch headlines. They reward people who notice when several unrelated stories suddenly share a thread. This week, three did. <span class="ticker" data-ticker="CRWV">CRWV</span>'s guidance miss put a question mark on AI capex. Trump rejected Iran's ceasefire response, sending Brent to $104. And the Russell 2000 has quietly outperformed the S&amp;P by ~6 percentage points year-to-date — a regime change that almost no retail investor is talking about. Each of those stories is interesting alone. The thread connecting them — that the market's narrow leadership is broadening, whether by stress or by rotation — is the actual story.</p>
    <p class="lede">Click anything <span class="term" data-term="underlined">underlined</span> for a definition. Click any <span class="ticker" data-ticker="DEMO">TICKER</span> for company detail with bull case, bear case, and what to watch. Every claim is tagged by confidence level (see legend below) so you know what's well-established versus what's interpretation.</p>
  `,

  daily: [],

  sections: [
    {
      id: 'section-1',
      number: '§ 01',
      title: 'What actually mattered',
      subtitle: 'Three stories filtered from a week of headlines. Each one moved capital in real ways. The rest was noise.',
      body: `
        <div class="news-item">
          <div class="kicker">Story No. 1 · AI Infrastructure</div>
          <h3 class="news-headline">CoreWeave guided below expectations. Now Nebius reports tomorrow, and the entire AI-cloud thesis is on the line.</h3>

          <p class="news-body"><span class="confidence confidence-fact">Fact</span> Last week, <span class="ticker" data-ticker="CRWV">CRWV</span> (CoreWeave) guided Q2 revenue to $2.45-2.6B — below the $2.69B Wall Street consensus — while raising 2026 <span class="term" data-term="capex">capital spending</span> to $31-35B. Q1 revenue more than doubled year-over-year to $2.1B, but the guidance miss caused a ~10% drop. The story isn't growth — it's that growth isn't keeping pace with spending.</p>

          <p class="news-body"><span class="confidence confidence-fact">Fact</span> Tomorrow (May 13), <span class="ticker" data-ticker="NBIS">NBIS</span> (Nebius) reports Q1. The consensus expects $316.9M revenue and an 81-cent loss. Nebius is the most direct competitor to CoreWeave. The stock is up <span class="data-callout">+431% over the past year</span> on a contracted backlog approaching $50B (including a $27B Meta deal and up to $19.4B from Microsoft). It trades at ~68x trailing sales.</p>

          <div class="news-why">Why this actually matters</div>
          <p class="news-body"><span class="confidence confidence-interp">Interp</span> For two years, the AI-cloud thesis has been "spending creates revenue, revenue justifies spending." If Nebius reports tomorrow with strong revenue but weak <span class="term" data-term="operating-leverage">operating leverage</span> — exactly what CoreWeave just showed — that's two data points in a row. Two data points in a row is the start of a trend. The names exposed: every AI-infrastructure pure-play, plus the second-derivative names (power, cooling, memory) that depend on this spending continuing.</p>

          <div class="timeframes">
            <div class="timeframe">
              <span class="timeframe-label">1 WEEK</span>
              <span class="timeframe-text">Nebius reports May 13 pre-market. Strong revenue beat with margin improvement = thesis intact, sentiment recovers. Revenue beat but margin compression = thesis cracking, sector under pressure. Revenue miss = entire AI-infra complex re-rates.</span>
            </div>
            <div class="timeframe">
              <span class="timeframe-label">3 MONTHS</span>
              <span class="timeframe-text"><span class="confidence confidence-interp">Interp</span> If Microsoft, Google, Meta, Amazon trim their AI spending plans for H2 2026 in their next earnings, the unwind moves from specialty cloud (CRWV, NBIS) to the hyperscalers themselves. That's the moment AI becomes a tactical question instead of a strategic one.</span>
            </div>
            <div class="timeframe">
              <span class="timeframe-label">1 YEAR</span>
              <span class="timeframe-text"><span class="confidence confidence-speculation">Spec</span> Either: (a) AI inference revenue scales fast enough to validate spending, and the picks-and-shovels names continue working; or (b) it doesn't, and we get a meaningful drawdown across the entire AI-adjacent complex. The honest answer is no one knows which yet — but the data points are starting to arrive.</span>
            </div>
          </div>

          <div class="positioning">
            <div class="positioning-label">How a sharp investor thinks about this</div>
            <span class="confidence confidence-interp">Interp</span> The smart positioning isn't a directional bet — it's relative-value. A pairs trade structure: long companies with profitable AI exposure (chip-makers with high margins, hyperscalers with proven monetization) vs. short companies still in spend-mode (specialty AI cloud, unprofitable infrastructure). Sharp money doesn't liquidate on one print; it shifts the mix. For a beginner: the lesson is that AI-related stocks are no longer one homogeneous trade. They've split into "profitable AI" and "spending AI", and those are now different bets.
          </div>
        </div>

        <div class="news-item">
          <div class="kicker">Story No. 2 · Geopolitics &amp; Oil</div>
          <h3 class="news-headline">Trump rejected Iran's ceasefire proposal as "totally unacceptable." Brent crude jumped to $104.</h3>

          <p class="news-body"><span class="confidence confidence-fact">Fact</span> On Sunday May 10, Iran responded to a U.S. ceasefire proposal demanding the lifting of sanctions, an end to the naval blockade, and recognition of Iranian sovereignty over the Strait of Hormuz. Trump rejected it publicly Monday, calling it "TOTALLY UNACCEPTABLE" and saying the ceasefire was "on life support." Brent crude jumped 2.7% to ~$104/barrel; WTI rose nearly 5% intraday to $100.30. The Strait remains largely closed to commercial traffic except for occasional confidence-building passages.</p>

          <p class="news-body"><span class="confidence confidence-fact">Fact</span> The war has now persisted for 72 days. <span class="confidence confidence-interp">Interp</span> Historical context: most "geopolitical premium" trades in oil reverse within 30-60 days as supply chains adapt. This one is now lasting long enough that elevated prices may be entering structural rather than premium territory. The market is starting to behave as if $100 oil is the new baseline, not a spike.</p>

          <div class="news-why">Why this actually matters</div>
          <p class="news-body"><span class="confidence confidence-interp">Interp</span> Oil at $100+ isn't an energy story — it's a macro story. It directly affects: (1) <span class="term" data-term="inflation">inflation</span> readings (gasoline, transport, food), (2) Fed policy (can they cut rates with oil this high?), (3) consumer spending (especially lower-income households), and (4) the bond market (longer-term Treasury yields). When you hear "oil at $104," translate it to: "the Fed probably can't cut rates this year, growth stocks face headwinds, energy stocks keep working, and the consumer K-shape deepens."</p>

          <div class="timeframes">
            <div class="timeframe">
              <span class="timeframe-label">1 WEEK</span>
              <span class="timeframe-text"><span class="confidence confidence-fact">Fact</span> CPI report drops this week. If hot, the rate-cut hopes evaporate. If cool, rates rally on hope. Either way, this is the most important data point of the month — and oil prices feed directly into it.</span>
            </div>
            <div class="timeframe">
              <span class="timeframe-label">3 MONTHS</span>
              <span class="timeframe-text"><span class="confidence confidence-interp">Interp</span> If Iran-US negotiations remain stalled into summer, we are looking at "stagflation-lite": slow growth, sticky inflation, no rate cuts. That environment is brutal for growth stocks, neutral-to-positive for energy/value, and ugly for long-duration assets (TLT, long bonds).</span>
            </div>
            <div class="timeframe">
              <span class="timeframe-label">1 YEAR</span>
              <span class="timeframe-text"><span class="confidence confidence-speculation">Spec</span> Resolution scenarios remain wildly open. A sudden peace deal would drop oil 15-25% in days. A widening conflict (Iran-Israel direct, or strikes on Saudi infrastructure) could push oil to $130+. Both outcomes have non-trivial probability. The honest position is "I don't know which, and neither does anyone else."</span>
            </div>
          </div>

          <div class="positioning">
            <div class="positioning-label">How a sharp investor thinks about this</div>
            <span class="confidence confidence-interp">Interp</span> The interesting setup is asymmetric protection, not directional bets. Energy stocks have priced in continued conflict — but a peace deal could erase 15-20% of those stocks' value in days. Sophisticated investors who are long energy are buying cheap downside protection (out-of-the-money puts on <span class="ticker" data-ticker="XLE">XLE</span>, calls on long-duration Treasuries). For a beginner: the lesson is that owning energy stocks right now means you're implicitly betting on continued conflict, whether you realize it or not. That's a geopolitics bet, not an energy bet.
          </div>
        </div>

        <div class="news-item">
          <div class="kicker">Story No. 3 · Market Structure</div>
          <h3 class="news-headline">The "Great Rotation" is real, ongoing, and almost nobody is talking about it.</h3>

          <p class="news-body"><span class="confidence confidence-fact">Fact</span> The Russell 2000 (small-cap index) is up ~8-9% year-to-date in 2026. The S&amp;P 500 is up modestly. For the first time in over a decade, small-caps are meaningfully outperforming mega-caps. The valuation gap that opened in 2024-2025 (S&amp;P 500 forward P/E ~26, Russell 2000 forward P/E ~18) is starting to close — not by mega-caps falling, but by small-caps rising.</p>

          <p class="news-body"><span class="confidence confidence-interp">Interp</span> Multiple forces driving this: (1) the OBBBA tax legislation restored 100% bonus depreciation and immediate R&amp;D expensing — a much bigger boost for capital-intensive small-caps than mega-caps; (2) Fed easing cycle benefits more-leveraged small-caps disproportionately; (3) AI buildout has shifted from "narrow hardware" to broader "real economy" beneficiaries (electrical, HVAC, construction). The Russell 2000 outperformed the Nasdaq for 10 consecutive sessions in January — the longest such streak in 30+ years.</p>

          <div class="news-why">Why this actually matters</div>
          <p class="news-body"><span class="confidence confidence-interp">Interp</span> When market leadership broadens from a narrow group of mega-caps to small/mid-caps, two things historically happen: (1) the bull market lasts longer (broader participation is healthier than narrow leadership); (2) the kinds of stocks that work change completely. The Magnificent Seven era was about owning a few names. The rotation era is about stock-picking among thousands.</p>

          <p class="news-body"><span class="confidence confidence-interp">Interp</span> For a beginner with an S&amp;P 500 index fund: you're underweighting the part of the market that's currently outperforming. Adding a small Russell 2000 allocation (e.g., <span class="ticker" data-ticker="IWM">IWM</span>) is one way to broaden exposure without picking individual names. <span class="confidence confidence-speculation">Spec</span> The historical analog is 2000-2006, when small-caps significantly outperformed for years after the dot-com bubble burst. Whether 2026 follows the same path is unknown, but the structural similarities are real.</p>

          <div class="timeframes">
            <div class="timeframe">
              <span class="timeframe-label">1 WEEK</span>
              <span class="timeframe-text">Watch whether the rotation continues if AI infrastructure names get hit (Nebius earnings). If small-caps hold while mega-caps wobble, the rotation thesis strengthens. If both fall, it's a different (and worse) story.</span>
            </div>
            <div class="timeframe">
              <span class="timeframe-label">3 MONTHS</span>
              <span class="timeframe-text"><span class="confidence confidence-interp">Interp</span> If Fed cuts materialize, small-caps' interest-rate sensitivity becomes a tailwind. If Fed pauses on inflation concerns, small-caps face refinancing pressure. The Fed's June meeting is the key event.</span>
            </div>
            <div class="timeframe">
              <span class="timeframe-label">1 YEAR</span>
              <span class="timeframe-text"><span class="confidence confidence-speculation">Spec</span> If the rotation is the start of a multi-year regime change (like 2000-2006), it has years to run. If it's a fakeout (like 2016, 2019, 2023, and other failed "rotation" calls), it reverses by Q3. Distinguishing between these in real time is one of the hardest things in markets.</span>
            </div>
          </div>
        </div>

        <div class="skipped">
          <div class="skipped-title">Headlines we ignored — and what they were trying to make you do</div>
          <ul>
            <li><strong>"Analyst raises Apple price target to $X"</strong> — Sell-side price targets follow stock prices, they don't lead them. The analyst is updating to match where the stock already is. Pure noise.</li>
            <li><strong>"S&amp;P 500 hits new all-time high"</strong> — Records happen routinely in bull markets. It's a milestone, not information. The day the market <em>stops</em> hitting new highs is the news, not when it does.</li>
            <li><strong>"Famous investor X just bought/sold Y"</strong> — Most quarterly 13F filings are 45+ days old by the time you see them. The position you're reading about may have already been exited.</li>
            <li><strong>"Hantavirus outbreak on cruise ship, Moderna jumps 7.5%"</strong> — Pandemic-trade reflex. Single-event vaccine spikes have historically faded within weeks. Unless you have specialty knowledge in infectious disease, this is gambling on a news cycle, not investing.</li>
            <li><strong>"Bitcoin down 7% YTD"</strong> — Crypto noise unless you're already in it. Bitcoin's correlation to equities is high enough that if you own stocks, you already have crypto-like risk in your portfolio without realizing it.</li>
            <li><strong>"Lumentum added to Nasdaq index"</strong> — Index inclusion adds passive buying mechanically, but the pop is usually priced in before announcement. Not a thesis, just plumbing.</li>
          </ul>
        </div>
      `
    },

    {
      id: 'section-2',
      number: '§ 02',
      title: 'Concept of the week',
      subtitle: 'Understanding why stocks move on earnings — and why "earnings beat" doesn\'t always mean "stock goes up."',
      body: `
        <div class="kicker">This week's concept</div>
        <div class="concept-callout">Stocks don't trade on results. They trade on results relative to expectations.</div>

        <p>This week, two companies reported earnings that "beat estimates" — and both their stocks fell. <span class="ticker" data-ticker="TTD">TTD</span> (The Trade Desk) beat on revenue and fell 14%. <span class="ticker" data-ticker="CRWV">CRWV</span> (CoreWeave) grew revenue 200% year-over-year and fell 10%. Meanwhile, <span class="ticker" data-ticker="OSCR">OSCR</span> (Oscar Health) beat earnings by 85% and the stock barely moved.</p>

        <p>If "good news = stock up" were the rule, none of this would make sense. The actual rule is far more interesting, and once you understand it, you'll never read an earnings report the same way again.</p>

        <p><strong>The thing professionals watch is not the number — it's the change in expectations.</strong> A stock's price reflects all known information and all expected future results. When a company reports, three things matter:</p>

        <ol style="margin: 16px 0 16px 28px; font-family: 'Fraunces', serif; font-size: 16px; line-height: 1.6;">
          <li><strong>The print</strong> — what they actually earned this quarter. Usually the least important.</li>
          <li><strong>The guidance</strong> — what they expect for next quarter and the year. Usually the most important.</li>
          <li><strong>The reaction relative to the setup</strong> — what was already priced in? If the stock was up 50% going in, an "in-line" print is a disappointment. If it was beaten down 40%, a small beat is a triumph.</li>
        </ol>

        <div class="example-box">
          <div class="label">Three real examples from this week</div>
          <p style="font-family: 'Fraunces', serif; font-size: 16px; line-height: 1.6; margin-bottom: 14px;"><strong><span class="ticker" data-ticker="TTD">TTD</span> beat revenue, fell 14%.</strong> Why? Because Q2 guidance was $750M vs. $772M consensus. The print was fine; the <em>forward expectations</em> were cut. Multiple analysts downgraded the next day. The stock fell on guidance, not on earnings.</p>

          <p style="font-family: 'Fraunces', serif; font-size: 16px; line-height: 1.6; margin-bottom: 14px;"><strong><span class="ticker" data-ticker="CRWV">CRWV</span> grew revenue 200% YoY, fell 10%.</strong> Why? Because growth of 200% wasn't enough when investors were modeling 220%+ implied by the capex they're spending. When you spend $30B+ to build capacity, the market expects revenue to follow. It didn't, fast enough.</p>

          <p style="font-family: 'Fraunces', serif; font-size: 16px; line-height: 1.6; margin-bottom: 0;"><strong><span class="ticker" data-ticker="OSCR">OSCR</span> beat EPS by 85%, stock barely moved.</strong> Why? Because the stock had already run +47% in 30 days going into the print. The good news was already priced in. Even a massive beat couldn't push it materially higher.</p>
        </div>

        <p style="margin-top: 24px;"><strong>What to do with this:</strong> Before any company you own reports earnings, check three things — (1) what's consensus expecting? (2) what's the stock done in the 30 days leading up? (3) what's management's history of guiding conservative vs. aggressive? A "beat" against low expectations on a beaten-down stock is bullish. A "beat" against high expectations on a stock that's already ripped is dangerous.</p>

        <p>This is also why the financial press gets earnings reactions wrong constantly. Headlines say "stock falls despite beating earnings — investors confused." Investors aren't confused. The headline writer is.</p>
      `
    },

    {
      id: 'section-3',
      number: '§ 03',
      title: 'A move dissected',
      subtitle: 'One stock move, traced from headline to underlying reason. Builds the most important investing skill: recognizing what\'s actually driving prices.',
      body: `
        <div class="dissection-card">
          <div class="dissection-meta">
            <span><strong>Ticker:</strong> <span class="ticker" data-ticker="TTD">TTD</span></span>
            <span><strong>Company:</strong> The Trade Desk</span>
            <span><strong>Move:</strong> <span class="move-indicator move-down">–14%</span></span>
            <span><strong>Date:</strong> May 8, 2026</span>
          </div>

          <div class="dissection-step">
            <div class="dissection-step-label">Step 1 · The headline reason</div>
            <p style="margin-bottom: 0;">"Trade Desk misses earnings expectations and provides weak Q2 guidance." This is what 90% of financial media reported. <span class="confidence confidence-fact">Fact</span> Adjusted EPS of $0.28 vs $0.32 expected. Q2 revenue guidance of $750M vs $772M consensus.</p>
          </div>

          <div class="dissection-step">
            <div class="dissection-step-label">Step 2 · What's underneath that headline</div>
            <p style="margin-bottom: 0;"><span class="confidence confidence-fact">Fact</span> Revenue growth has decelerated from 25% YoY in Q1 2025, to 14% in Q4 2025, to 12% in Q1 2026 — and Q2 guidance implies just ~8%. <span class="confidence confidence-interp">Interp</span> That's not a "soft quarter." That's a clear, sustained deceleration of growth that has been happening for over a year. The market is finally pricing it in.</p>
          </div>

          <div class="dissection-step">
            <div class="dissection-step-label">Step 3 · The actual structural story</div>
            <p style="margin-bottom: 0;"><span class="confidence confidence-interp">Interp</span> The Trade Desk built the leading independent demand-side platform for digital advertising. Their pitch: agencies and brands can buy ads programmatically across the entire open web through them, instead of going directly to Google or Meta. That model is being challenged from two directions: (1) <strong>walled gardens</strong> — Google, Meta, and Amazon are capturing more ad dollars directly, bypassing intermediaries; (2) <strong>retail media networks</strong> — Walmart, Amazon, Target, and others are building their own ad networks that don't need TTD. Plus, Publicis (a major ad agency) reportedly advised clients against TTD in March. This is not a "missed quarter." It's a thesis-changing structural shift.</p>
          </div>

          <div class="dissection-step">
            <div class="dissection-step-label">Step 4 · What it means for sharp investors vs. retail investors</div>
            <p style="margin-bottom: 0;"><span class="confidence confidence-interp">Interp</span> A sharp investor read this print and asked: "Is this a quality company that hit a rough patch (in which case down 14% is opportunity), or is this a structural decline (in which case down 14% is just the start)?" The downgrades from KeyBanc, Oppenheimer, and William Blair all explicitly cited <em>structural</em> factors — not cyclical ones. That's the tell. <span class="confidence confidence-speculation">Spec</span> When sell-side analysts who were bullish suddenly use the word "structural" to describe a thesis change, the stock typically has further to fall before it bottoms.</p>
          </div>

          <div class="dissection-step">
            <div class="dissection-step-label">Step 5 · The lesson</div>
            <p style="margin-bottom: 0;">The financial press will tell you why a stock moved <em>today</em>. That answer is rarely the real one. The real reason is usually a slower-moving structural force — competition, business model change, technological shift — that was visible for months before today's print. Your job as an investor is to read past the headline and ask: "What does this print tell me about what's been quietly happening for a while?"</p>
          </div>
        </div>

        <p style="font-style: italic; color: var(--ink-muted); font-size: 15px; margin-top: 24px;">In future briefs, this section will dissect a different move each week — sometimes a winner, sometimes a loser. Over time, you'll start to see the recurring patterns: deceleration prints, structural-shift prints, sentiment-flush prints, narrative-change prints. The patterns are finite, and recognizing them is most of the skill.</p>
      `
    },

    {
      id: 'section-4',
      number: '§ 04',
      title: 'Sectors that mattered',
      subtitle: 'Only the sectors where something genuinely happened. Equal coverage of every sector dilutes the signal.',
      body: `
        <h3 class="subsection-title">Healthcare</h3>
        <p class="subsection-tagline">The contrarian setup we flagged last week is starting to pay off — for one specific subsector.</p>

        <p><span class="confidence confidence-fact">Fact</span> Healthcare is the only S&amp;P 500 sector still showing year-over-year earnings declines in Q1 2026. <span class="confidence confidence-fact">Fact</span> But within that picture, individual names are diverging sharply. <span class="ticker" data-ticker="OSCR">OSCR</span> (Oscar Health) reported Q1 EPS of $2.07 vs $1.12 expected — an 85% beat. Net income hit a record $679M. Stock has run +47% in 30 days, +65% in 90 days. Membership grew to 3.17M.</p>

        <p><span class="confidence confidence-interp">Interp</span> What's happening in Oscar isn't really about Oscar. It's about the <em>individual health insurance market</em> — people buying insurance through ACA exchanges rather than through employers. That market is growing because: (1) the workforce is shifting (more gig workers, contractors, small business owners); (2) Oscar uses technology to lower operating costs vs. legacy insurers; (3) the medical loss ratio improved from 75.4% to 70.5% — meaning more of each premium dollar is profit. The thesis: tech-enabled insurance is taking share from legacy insurers, and it's just getting started.</p>

        <div class="example-box">
          <div class="label">A genuinely interesting opportunity setup</div>
          <p style="margin-bottom: 0; font-family: 'Fraunces', serif; font-size: 16px; line-height: 1.6;">Oscar trades at a P/S (price-to-sales) of ~0.5x versus 0.7-1.1x for peers. The stock has run hard, but it's still cheaper than legacy insurers on most fundamental measures. <span class="confidence confidence-speculation">Spec</span> If management's $250-450M operating earnings guidance holds, and revenue hits the $18.7-19B range, this is a stock with significant operating leverage that the market is just starting to recognize. Worth doing real homework on. Click the ticker for more.</p>
        </div>

        <hr style="border: none; border-top: 1px solid var(--rule); margin: 48px 0 32px;">

        <h3 class="subsection-title">Energy</h3>
        <p class="subsection-tagline">No longer "rallying on news" — the market is starting to price elevated oil as a structural condition.</p>

        <p><span class="confidence confidence-fact">Fact</span> WTI sits at ~$98-100, Brent at ~$104. The XLE energy sector ETF rose 37% in Q1 2026. Major beneficiaries: <span class="ticker" data-ticker="APA">APA</span> (+73% Q1), <span class="ticker" data-ticker="TPL">TPL</span> (+65%), <span class="ticker" data-ticker="OXY">OXY</span> (+58%).</p>

        <p><span class="confidence confidence-interp">Interp</span> Here's the more interesting observation: in the past week, despite oil rallying further on the failed ceasefire, energy stocks didn't move proportionally. That divergence usually means one of two things: (1) the easy gains are gone and the market is starting to price in geopolitical resolution risk, or (2) sector rotation is happening — money is moving out of energy and into something else even as oil rises. <span class="confidence confidence-speculation">Spec</span> Either interpretation argues for being less excited about energy from here, despite the oil price.</p>

        <p>The opportunity in energy this week is not "buy more." It's "if I own energy, am I prepared for the down case?" A peace deal headline tomorrow could cut these stocks 15-20% in days.</p>

        <hr style="border: none; border-top: 1px solid var(--rule); margin: 48px 0 32px;">

        <h3 class="subsection-title">Technology</h3>
        <p class="subsection-tagline">Splitting into "profitable AI" and "spending AI" — and the gap is widening.</p>

        <p><span class="confidence confidence-fact">Fact</span> The big tell this week was differentiation within tech. <span class="ticker" data-ticker="AMD">AMD</span> beat Q1 and rose 2.4% — measured response to a measured beat. <span class="ticker" data-ticker="NVDA">NVDA</span> trades near highs on continued data center demand. <span class="ticker" data-ticker="CRWV">CRWV</span> fell 10% on guidance. <span class="ticker" data-ticker="TTD">TTD</span> fell 14% on structural concerns. <span class="ticker" data-ticker="NBIS">NBIS</span> hits highs ahead of its Wednesday report.</p>

        <p><span class="confidence confidence-interp">Interp</span> The era of "buy any AI-related stock" is ending. What's replacing it: discrimination between companies that have profitable AI exposure (chip makers, established hyperscalers, software companies with clear monetization) and companies that are still spending heavily without proven returns (specialty AI clouds, unprofitable infrastructure plays). The market is starting to price these differently — finally.</p>

        <p><strong>The key tell:</strong> Watch how the market reacts to Nebius tomorrow. If they beat revenue but face the same operating leverage concerns as CoreWeave, "spending AI" gets re-rated lower. If they show genuine margin improvement, the thesis lives another quarter.</p>

        <div class="quiet">
          <div class="quiet-title">Other sectors, briefly</div>
          <div class="quiet-item"><strong>Financials:</strong> No major moves. Banks remain quiet beneficiaries of the steepening yield curve. <span class="confidence confidence-interp">Interp</span> The risk we flagged last week (banks' exposure to AI-infrastructure lending) hasn't shown up in data yet, but if AI capex slowdown continues, it's a 2-3 quarter delayed concern.</div>
          <div class="quiet-item"><strong>Consumer:</strong> <span class="ticker" data-ticker="DG">DG</span> (Dollar General) fell 5.8% on soft guidance and a CEO transition. <span class="confidence confidence-interp">Interp</span> Even at the deep-discount end of the K-shape (where you'd expect to win from consumer trade-down), execution challenges are showing up. The K-shape isn't a uniform tailwind for discounters — quality matters.</div>
          <div class="quiet-item"><strong>Industrials:</strong> AI-infrastructure beneficiaries (<span class="ticker" data-ticker="PWR">PWR</span>, <span class="ticker" data-ticker="GEV">GEV</span>) continue at extreme valuations. No major moves this week, but they remain at risk if the AI infra thesis cracks.</div>
          <div class="quiet-item"><strong>Communication Services:</strong> Largest contributor to overall S&amp;P earnings beat this quarter. Alphabet, Netflix, Meta all crushed Q1 estimates. Quiet because the leadership is so established, but the earnings are the strongest in the index.</div>
        </div>
      `
    },

    {
      id: 'section-5',
      number: '§ 05',
      title: 'Pattern recognition',
      subtitle: 'Markets repeat patterns more than they admit. This week\'s pattern is one of the most important ones to recognize.',
      body: `
        <div class="kicker">This week's pattern</div>
        <div class="concept-callout">"The first crack" — when one company in a hot theme misses, watch what the market does to the next one.</div>

        <p>One of the most reliable patterns in markets: when a hot theme is fully consensus, the first company to disappoint creates an immediate test. The question is whether the next company in line confirms the issue, or whether the first miss was idiosyncratic.</p>

        <p><strong>The pattern:</strong> Hot theme runs for months. First company misses or guides weakly. Stock falls 10-15%. The other companies in the theme initially dip in sympathy but quickly recover. Then the second-most-similar company reports. <em>This is the actual moment of truth.</em></p>

        <ul style="margin: 16px 0 16px 24px; font-family: 'Fraunces', serif; font-size: 16px; line-height: 1.65;">
          <li>If the second company prints clean and the first miss looks isolated, the theme survives. The sector recovers.</li>
          <li>If the second company shows similar weakness, the theme is in trouble. The whole complex re-rates lower.</li>
        </ul>

        <p><span class="confidence confidence-interp">Interp</span> Historical examples of this pattern playing out:</p>

        <ul style="margin: 12px 0 16px 24px; font-family: 'Fraunces', serif; font-size: 16px; line-height: 1.65;">
          <li><strong>Snowflake's first guidance cut (2022)</strong> → followed by similar weakness in MongoDB, Datadog, others. The "data cloud" theme re-rated lower across the board.</li>
          <li><strong>Peloton's first sales miss (2021)</strong> → confirmed by other COVID-beneficiary names. The "pandemic stocks" trade unwound over the next year.</li>
          <li><strong>Cisco's first guide-down (early 2000)</strong> → confirmed by every other dot-com infrastructure name. The bubble's first definitive cracks appeared in earnings, not in stock prices.</li>
        </ul>

        <p>This week, we're watching exactly this pattern develop in AI infrastructure. <span class="ticker" data-ticker="CRWV">CRWV</span> was the first crack. <span class="ticker" data-ticker="NBIS">NBIS</span> tomorrow is the confirmation test.</p>

        <div class="positioning">
          <div class="positioning-label">How to use this pattern as an investor</div>
          <span class="confidence confidence-interp">Interp</span> Don't immediately sell on the first crack — markets often shrug them off. Don't immediately buy the dip on the first crack either — sometimes it's the leading edge. The right action is to <em>wait for the confirmation test</em>. If the second company confirms the weakness, you have time to reduce exposure or open downside hedges. If it doesn't, the dip in the first name often becomes a real buying opportunity. The pattern rewards patience, not reflexes.
        </div>
      `
    },

    {
      id: 'section-6',
      number: '§ 06',
      title: 'The story tracker',
      subtitle: 'Themes don\'t develop in a single week. Here\'s what we\'re tracking and how each one moved since last issue.',
      body: `
        <div class="story">
          <h3 class="story-title">Is the AI spending boom slowing down?</h3>
          <div class="story-meta">Tracking since Issue #1 · Status: <span class="story-status status-test">Test Tomorrow</span></div>
          <p style="font-size: 16px;">Last week we flagged CoreWeave as the "first crack." This week, the confirmation test arrives: Nebius reports tomorrow (May 13). This story now moves from "watching" to "active."</p>
          <p class="story-progress">Movement since last issue: Significant. The thesis went from "maybe a concern" to "the next earnings print resolves it."</p>
        </div>

        <div class="story">
          <h3 class="story-title">Will the Iran conflict resolve, and when?</h3>
          <div class="story-meta">Tracking since Issue #1 · Status: <span class="story-status status-cracking">Worsened</span></div>
          <p style="font-size: 16px;">Last week: tankers cautiously crossing Hormuz; markets pricing some resolution probability. This week: Trump publicly rejected Iran's response, calling it "totally unacceptable." Brent at $104. The ceasefire is now described by the President as "on life support." Conflict is now 72 days old — longer than most geopolitical premium trades historically last.</p>
          <p class="story-progress">Movement since last issue: Negative. Resolution probability decreased, baseline of $100+ oil hardening into expectations.</p>
        </div>

        <div class="story">
          <h3 class="story-title">The Great Rotation: small-caps over mega-caps</h3>
          <div class="story-meta">New this issue · Status: <span class="story-status status-developing">Active</span></div>
          <p style="font-size: 16px;">Added this week because it's been quietly happening since January and deserves attention. Russell 2000 up ~8-9% YTD vs S&amp;P 500 up modestly. OBBBA tax provisions, Fed easing, and AI buildout broadening are the drivers. Whether this is structural (multi-year) or another fakeout (reverses by Q3) is the key question.</p>
          <p class="story-progress">Movement since last issue: New tracking. Will watch month-over-month relative performance of IWM vs SPY.</p>
        </div>

        <div class="story">
          <h3 class="story-title">Is the K-shape consumer becoming permanent?</h3>
          <div class="story-meta">Tracking since Issue #1 · Status: <span class="story-status status-watching">Watching</span></div>
          <p style="font-size: 16px;">No major new data this week. Retail sales report this week is the key data point. <span class="ticker" data-ticker="DG">DG</span> (Dollar General) softness suggests even the deep-discount end of consumer is facing pressure, which complicates a simple "K-shape = own Walmart and Costco" thesis.</p>
          <p class="story-progress">Movement since last issue: Slightly negative (DG softness). Awaiting retail sales data.</p>
        </div>

        <div class="story">
          <h3 class="story-title">Will the Fed cut rates in 2026?</h3>
          <div class="story-meta">Tracking since Issue #1 · Status: <span class="story-status status-cracking">Cracking</span></div>
          <p style="font-size: 16px;">Oil at $104 makes the Fed's job significantly harder. Markets had been pricing one cut in 2026; that probability is now lower. <span class="confidence confidence-speculation">Spec</span> If May CPI comes in hot, the next move is "Fed pauses, possibly hawkish surprise" rather than "Fed cuts." That repricing has not fully happened yet.</p>
          <p class="story-progress">Movement since last issue: Lower probability of cuts. CPI report this week is the next major data point.</p>
        </div>

        <div class="story">
          <h3 class="story-title">Healthcare: rotation candidate or value trap?</h3>
          <div class="story-meta">Tracking since Issue #1 · Status: <span class="story-status status-confirmed">Partially Confirmed</span></div>
          <p style="font-size: 16px;">Oscar Health's massive Q1 beat and 47% one-month run suggests that within healthcare, there are real opportunities being missed. <span class="confidence confidence-interp">Interp</span> The "unloved sector becoming the next leadership" thesis is starting to show signs in <em>specific names</em> rather than across the whole sector. The contrarian setup is real, but selective.</p>
          <p class="story-progress">Movement since last issue: Positive. The thesis is starting to show evidence, but in a more granular way than expected.</p>
        </div>
      `
    },

    {
      id: 'section-7',
      number: '§ 07',
      title: 'Your toolkit',
      subtitle: 'Tool №02 this week. Over 52 weeks, this builds into a real framework for thinking about markets.',
      body: `
        <div class="tool">
          <div class="tool-number">TOOL № 02 · NEW THIS WEEK</div>
          <h3 class="tool-name">The Earnings Reaction Decoder</h3>
          <p style="margin-bottom: 12px;">Before any company you own (or are considering) reports earnings, ask these five questions. They'll prevent you from being confused by reactions that look irrational on the surface.</p>
          <ol>
            <li><strong>What does consensus expect?</strong> Both for this quarter and forward guidance. Without knowing the bar, you can't tell if it was cleared.</li>
            <li><strong>What has the stock done in the last 30 days?</strong> A stock up 20% into earnings has a much higher implicit bar than one down 20%.</li>
            <li><strong>What's management's history with guidance?</strong> Some companies (Trade Desk historically, NVDA) consistently sandbag and beat. Others (Salesforce, traditionally) guide aggressively and sometimes miss. Same number, different meaning.</li>
            <li><strong>What's the most-watched single metric?</strong> For SaaS companies it's often net revenue retention. For chipmakers it's data center revenue. For banks it's net interest income. Whatever it is, that's what moves the stock.</li>
            <li><strong>What would the bear case need to see to be confirmed or denied?</strong> If you're long, you need to know in advance what would change your mind. Earnings is when you find out.</li>
          </ol>
          <div class="tool-meta">Keep this checklist somewhere you'll see it before any earnings you care about. Even doing this exercise without acting on it makes you a sharper reader of markets within a few quarters.</div>
        </div>

        <div class="toolkit-history">
          <h4>Toolkit so far · The list grows each week</h4>
          <p>Tool № 01 — The Four Questions Before Buying Any Stock (Issue #1)</p>
          <p>Tool № 02 — The Earnings Reaction Decoder (Issue #2)</p>
        </div>
      `
    },

    {
      id: 'section-8',
      number: '§ 08',
      title: 'The week ahead',
      subtitle: 'Four specific things to watch this week, why each matters, and what to learn from each one.',
      body: `
        <div class="news-item">
          <h3 class="news-headline">Wednesday, May 13 (pre-market): Nebius Q1 earnings</h3>
          <p class="news-body">The single most important market event of the week. Consensus: $316.9M revenue, $(0.81) EPS. The bigger questions: revenue trajectory toward 2026 ARR target of $7-9B, EBITDA margin progression, and any commentary on Eigen AI integration.</p>
          <p class="news-body"><strong>What to learn:</strong> Watch the market's <em>first 30 minutes</em> of reaction. That's professionals making real decisions on real information. The narrative in the financial media will lag the price action by hours. The price action is the truth.</p>
        </div>

        <div class="news-item">
          <h3 class="news-headline">This week: CPI report (April data)</h3>
          <p class="news-body">The main inflation reading. Core CPI is the most-watched number. Above expectations = Fed cuts off the table, equities sell off. Below expectations = rate-cut hopes revive, equities rally. The Iran conflict at $104 oil makes this print harder to predict than usual.</p>
          <p class="news-body"><strong>What to learn:</strong> Notice which sectors react most. Banks usually love higher rates (NIM expands). Long-duration tech hates them. Consumer staples and energy are relatively insulated. The pattern of reactions teaches you the plumbing.</p>
        </div>

        <div class="news-item">
          <h3 class="news-headline">This week: Retail sales report</h3>
          <p class="news-body">The cleanest data on actual consumer behavior. Breakdown by category matters more than the headline. Strong electronics + weak clothing = trade-down. Strong restaurants + weak grocery = wealthy still spending. Each combination tells a different story about the K-shape.</p>
          <p class="news-body"><strong>What to learn:</strong> Don't just read "retail sales up 0.3%." Read the components. The professionals read the components.</p>
        </div>

        <div class="news-item">
          <h3 class="news-headline">Any Iran headline</h3>
          <p class="news-body">The ceasefire is described by Trump as "on life support." Any movement in either direction (concession or escalation) will move oil $3-7 in minutes and ripple through every sector. Watch how energy stocks react relative to oil itself — if they decouple, that's a signal the market is starting to discount the geopolitical premium.</p>
          <p class="news-body"><strong>What to learn:</strong> When unrelated assets start moving together, it tells you what the market actually cares about. Oil up + Treasuries down + dollar up + gold up = stagflation fear. Oil up + Treasuries up + dollar down = recession fear. Same oil move, completely different message.</p>
        </div>
      `
    }
  ]
});
