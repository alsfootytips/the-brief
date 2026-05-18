window.theBrief = window.theBrief || { issues: [] };

window.theBrief.issues.push({
  number: 3,
  date: 'Week of May 19, 2026',
  thesis: `The bull market just collided with three things in a single week — the hottest inflation in three years, a new Fed Chair confirmed by the slimmest margin in history, and a Trump-Xi summit that produced one airplane order. It survived the collision because Q1 earnings keep doing the work and the AI capex thesis just got a fresh vote of confidence from Nebius. The story isn't the price action. It's that the bull case has narrowed to one beam: earnings.`,

  lede: `
    <p class="lede drop-cap">Markets had every reason to fall this week and rose anyway — until Friday, when they remembered why. April CPI printed at 3.8%, the hottest in three years. <span class="ticker" data-ticker="NBIS">NBIS</span> blew out earnings and went to an all-time high. Kevin Warsh was confirmed as the next Fed Chair by a 54-45 vote — the narrowest in Fed history — and then walked into a job where the data makes rate cuts impossible. Trump and Xi met in Beijing for two days and produced a Boeing order. By Friday's close, the six-week win streak was over. None of that is bearish on its own. What it adds up to is harder: the bull case is now running on earnings alone, with every other support beam (Fed cuts, trade clarity, valuation cushion) kicked out.</p>
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
          <div class="kicker">Story No. 1 · Inflation</div>
          <h3 class="news-headline">April CPI came in at 3.8% — the highest reading in three years. The Fed's hands just got tied.</h3>

          <p class="news-body"><span class="confidence confidence-fact">Fact</span> Headline CPI rose 3.8% year-over-year in April, above the 3.7% expected and well above March's 3.3%. Core CPI (excluding food and energy) was up 2.8% YoY and 0.4% month-over-month — still above the Fed's 2% target. Energy prices accounted for roughly 40% of the increase. Shelter and food also rose meaningfully.</p>

          <p class="news-body"><span class="confidence confidence-fact">Fact</span> The market response was immediate and total. Traders moved from pricing in roughly one rate cut in 2026 to pricing in a <span class="data-callout">better than 1-in-3 chance of a rate hike</span> by year-end. The probability of any cut between now and the end of 2027 effectively collapsed to zero.</p>

          <div class="news-why">Why this actually matters</div>
          <p class="news-body"><span class="confidence confidence-interp">Interp</span> For two years, the equity market has been priced for a Fed easing cycle. Most growth stocks, long-duration assets, and small-caps carry an implicit assumption of falling rates somewhere in their valuation. A 3.8% print doesn't just delay cuts — it reverses the direction of travel. The Fed cannot credibly cut rates with inflation running 90% above target. And if energy stays elevated (more on that below), May's print won't be much better.</p>

          <p class="news-body"><span class="confidence confidence-interp">Interp</span> The honest reading: the "soft landing" narrative that dominated 2024-2025 is being replaced — in real time — by something closer to "stickier inflation, no relief from the Fed." That doesn't mean recession. It means a regime where bond yields stay higher than expected, growth multiples compress, and the burden of producing returns shifts entirely onto earnings growth.</p>

          <div class="timeframes">
            <div class="timeframe">
              <span class="timeframe-label">1 WEEK</span>
              <span class="timeframe-text">Watch the 10-year Treasury yield. If it pushes through 4.7%, growth stocks face real pressure regardless of company-specific news. FOMC minutes drop this week — read carefully for how many members already wanted to be more hawkish before the April print.</span>
            </div>
            <div class="timeframe">
              <span class="timeframe-label">3 MONTHS</span>
              <span class="timeframe-text"><span class="confidence confidence-interp">Interp</span> If May and June CPI confirm the April pattern, the narrative shifts from "Fed pause" to "Fed hike risk." That's a meaningfully different market — financials become winners, long-duration tech faces sustained pressure, and the dollar likely strengthens against developed-market currencies.</span>
            </div>
            <div class="timeframe">
              <span class="timeframe-label">1 YEAR</span>
              <span class="timeframe-text"><span class="confidence confidence-speculation">Spec</span> The harder question: is this a transitory bounce driven by energy, or the start of a structurally higher inflation regime (tariffs, reshoring, demographics, energy)? Markets have priced the former. If it turns out to be the latter, every long-duration asset in the market is mispriced. The next two CPI prints settle it.</span>
            </div>
          </div>

          <div class="positioning">
            <div class="positioning-label">How a sharp investor thinks about this</div>
            <span class="confidence confidence-interp">Interp</span> A sharp investor isn't reacting to one print — they're watching for a <em>regime change</em>. The right question after April CPI isn't "should I sell?" It's "what positions in my portfolio require falling rates to work?" Long-duration tech without near-term earnings, REITs, utilities, leveraged small-caps, long Treasuries — those are the rate-sensitive bucket. Energy, financials, defense, short-duration cash flows — those work better in a higher-for-longer world. The action isn't selling; it's rebalancing the mix.
          </div>
        </div>

        <div class="news-item">
          <div class="kicker">Story No. 2 · The Fed</div>
          <h3 class="news-headline">Kevin Warsh was confirmed as Fed Chair by a 54-45 vote — the narrowest margin in Fed history. He just inherited an impossible job.</h3>

          <p class="news-body"><span class="confidence confidence-fact">Fact</span> The Senate confirmed Kevin Warsh as the next Federal Reserve Chair on Wednesday, May 13, by a 54-45 vote — mostly along party lines, with only Democratic Sen. John Fetterman crossing over. The margin is the slimmest in the history of the Fed Chair role. Warsh replaced Jerome Powell on May 15. His first FOMC meeting as chair will be June 16-17.</p>

          <p class="news-body"><span class="confidence confidence-fact">Fact</span> Warsh was Trump's hand-picked nominee. Markets initially read the appointment as dovish — Trump has publicly pressured the Fed to cut rates aggressively, and Warsh was assumed to be more responsive to that pressure than Powell. The April CPI print, released the day before Warsh's confirmation, complicated that read immediately.</p>

          <p class="news-body"><span class="confidence confidence-fact">Fact</span> The Fed's most recent decision (April, under Powell) held rates at 3.50-3.75%, but the vote was unusually fractured — 8-4, with three members objecting to <em>removing</em> the language about eventual cuts. It was the first time since October 1992 that four officials dissented.</p>

          <div class="news-why">Why this actually matters</div>
          <p class="news-body"><span class="confidence confidence-interp">Interp</span> The market wants to interpret Warsh as dovish. The data is forcing him to be hawkish. That's the central tension of the next six months. A Fed Chair confirmed by the narrowest margin in history, appointed under political pressure to cut, faces a CPI print that makes cutting indefensible. Either he cuts and loses institutional credibility, or he holds (or hikes) and disappoints the President who appointed him. Both paths have political consequences. Neither has good market consequences in the near term.</p>

          <p class="news-body"><span class="confidence confidence-interp">Interp</span> What the market hasn't fully priced: the <em>uncertainty premium</em> attached to a politicized Fed transition. When the Fed Chair's independence is in genuine question, long-end Treasury yields tend to rise (investors demand more compensation for inflation risk). That's already happening at the margin. It's likely to continue regardless of what Warsh actually does, because the question itself is the problem.</p>

          <div class="timeframes">
            <div class="timeframe">
              <span class="timeframe-label">1 WEEK</span>
              <span class="timeframe-text">Warsh's first public remarks as Chair will move markets more than the content deserves. Watch for two things: (1) does he commit to "data dependence" language Powell used, and (2) does he reference the FOMC's 2% target directly. Both are credibility signals.</span>
            </div>
            <div class="timeframe">
              <span class="timeframe-label">3 MONTHS</span>
              <span class="timeframe-text"><span class="confidence confidence-interp">Interp</span> The June FOMC is the first real test. If Warsh holds with hawkish language, the dovish-Warsh narrative dies and the dollar/bonds rally. If he cuts in defiance of inflation data, the long end of the curve sells off hard (yields up) and gold/bitcoin/foreign currencies catch a structural bid.</span>
            </div>
            <div class="timeframe">
              <span class="timeframe-label">1 YEAR</span>
              <span class="timeframe-text"><span class="confidence confidence-speculation">Spec</span> The deeper question — whether "Fed independence" survives this presidential term — won't be answered in 12 months. But the answer starts being written this summer. Investors who lived through 1970s stagflation will tell you: the moment markets stop trusting the central bank is the moment everything reprices. We're nowhere near that. But we're closer than we were a year ago.</span>
            </div>
          </div>

          <div class="positioning">
            <div class="positioning-label">How a sharp investor thinks about this</div>
            <span class="confidence confidence-interp">Interp</span> The sharp money is hedging tail risk cheaply. Long-dated puts on TLT (long-duration Treasuries), small allocations to gold and bitcoin, and reduced exposure to the longest-duration growth names. None of those are "the trade" — they're insurance against the regime change you can't predict. For a beginner: the lesson isn't to bet on hyperinflation. It's to notice that the assumed support beam of "the Fed has our backs" is structurally weaker than it was, and adjust position sizing accordingly.
          </div>
        </div>

        <div class="news-item">
          <div class="kicker">Story No. 3 · Geopolitics</div>
          <h3 class="news-headline">Trump and Xi met for two days in Beijing and produced one airplane order. Friday's selloff was the market scoring the summit.</h3>

          <p class="news-body"><span class="confidence confidence-fact">Fact</span> The Trump-Xi summit ran May 14-15 in Beijing. The concrete outcomes: an order for 200 Boeing aircraft, a Chinese commitment to allow imports of American beef, and broad statements about agricultural purchases. Both sides agreed to preserve the existing tariff truce and establish a trade council and an investment council. The summit statements released by the two governments overlapped in limited areas; significant items appeared in one side's readout but not the other's.</p>

          <p class="news-body"><span class="confidence confidence-fact">Fact</span> The market response on Friday: S&amp;P 500 -1.24% to 7,408.50, Nasdaq -1.54% to 26,225.14, Dow -1.07% to 49,526.17. That ended a six-week winning streak — the longest for both the S&amp;P and Nasdaq since 2024. Treasury yields rose on the day.</p>

          <div class="news-why">Why this actually matters</div>
          <p class="news-body"><span class="confidence confidence-interp">Interp</span> Markets had quietly priced in a meaningful tariff-relief outcome from the summit. The reasoning was simple: both sides have economic incentives to de-escalate, both leaders wanted a "deal" to claim, and a Beijing visit by a U.S. President is rare enough that markets assumed it was telegraphed. The actual outcome — handshakes, one airplane order, and twin statements that don't agree on what was agreed — was meaningfully below expectations. Friday's selloff is the market repricing.</p>

          <p class="news-body"><span class="confidence confidence-interp">Interp</span> The bigger picture: the "trade truce" remains in place, but no progress was made toward unwinding the underlying tariff structure. For companies with significant China exposure — semiconductors, industrials, consumer goods that source from China — the operating environment doesn't get easier. The tariff overhang stays. Combine that with the CPI print, and you have a worse setup for multinationals than the market was assuming a week ago.</p>

          <div class="timeframes">
            <div class="timeframe">
              <span class="timeframe-label">1 WEEK</span>
              <span class="timeframe-text">Watch China-exposed names this week. If <span class="ticker" data-ticker="NVDA">NVDA</span> guides cautiously on China when it reports Tuesday, that confirms the tariff overhang is still material. Watch industrials (CAT, DE) and semiconductor equipment (AMAT, LRCX) for similar signals.</span>
            </div>
            <div class="timeframe">
              <span class="timeframe-label">3 MONTHS</span>
              <span class="timeframe-text"><span class="confidence confidence-interp">Interp</span> Without a concrete tariff-relief catalyst on the calendar, the path of least resistance is "tariffs continue to grind into margins." Q2 earnings (July-August) will be the first quarter where the full impact of the current tariff regime shows up in numbers. That's the moment the market actually scores the cost.</span>
            </div>
            <div class="timeframe">
              <span class="timeframe-label">1 YEAR</span>
              <span class="timeframe-text"><span class="confidence confidence-speculation">Spec</span> Two paths from here. Path A: another summit later in 2026 produces a real deal, and tariffs come down meaningfully — a clear positive for cyclicals, multinationals, and emerging markets. Path B: the trade-council framework becomes the new permanent normal — tariffs as managed friction, not crisis, but also not relief. Path B is more probable in our read, but Path A is the bigger market mover if it lands.</span>
            </div>
          </div>
        </div>

        <div class="skipped">
          <div class="skipped-title">Headlines we ignored — and what they were trying to make you do</div>
          <ul>
            <li><strong>"S&amp;P hits sixth straight weekly gain — longest streak since 2024"</strong> — Streaks make for clicks. They don't predict anything. The streak broke on Friday, which is news; the streak itself was just a tally.</li>
            <li><strong>"Cisco surges 15% on AI orders"</strong> — Worth noting, not worth chasing. The 15% pop happened in 30 minutes after the print. Anyone reading about it the next day was buying from someone who already had the position.</li>
            <li><strong>"Bitcoin volatile around CPI"</strong> — Crypto trades on the same macro inputs as everything else right now. Headlines pretending it's a unique signal are usually the headline writer not knowing what else to write.</li>
            <li><strong>"Analyst raises Nvidia price target ahead of earnings"</strong> — Sell-side analysts almost never want to be cautious into a likely-good print. The price target raise is positioning, not insight. Read the actual report (some have real substance), ignore the headline.</li>
            <li><strong>"Trump says 'fantastic trade deals' after Beijing"</strong> — Statements by politicians at the end of summits are theater. The market signal is in what got <em>signed</em>, not what was said. Boeing order: signed. Everything else: rhetoric.</li>
          </ul>
        </div>
      `
    },

    {
      id: 'section-2',
      number: '§ 02',
      title: 'Concept of the week',
      subtitle: 'Understanding why a dovish Fed Chair cannot deliver dovish policy when the data won\'t cooperate.',
      body: `
        <div class="kicker">This week's concept</div>
        <div class="concept-callout">A central bank's credibility is the product of two things: its independence, and its willingness to take pain. Both are tested this summer.</div>

        <p>Markets have spent six months treating Kevin Warsh's nomination as a dovish signal. The thinking went: Trump wants lower rates, Warsh was chosen by Trump, therefore Warsh will cut rates. That logic is intuitive and probably wrong — and understanding <em>why</em> it's wrong is one of the most important frameworks an investor can build.</p>

        <p><strong>The Fed Chair's mandate isn't to please the President. It's to maintain the credibility of the dollar.</strong> When the Fed cuts rates while inflation is materially above target, three things happen — fast.</p>

        <ol style="margin: 16px 0 16px 28px; font-family: 'Fraunces', serif; font-size: 16px; line-height: 1.6;">
          <li><strong>The long end of the yield curve sells off.</strong> Bond investors don't care what the Fed Funds rate is — they care about expected inflation over the next 10-30 years. If the Fed signals it will tolerate inflation, the 10-year and 30-year yields go <em>up</em>, not down. Cutting short rates while long rates rise is a curve steepener — and it makes mortgages, corporate debt, and government borrowing more expensive, not less.</li>
          <li><strong>The dollar weakens.</strong> Foreign capital that's been parking in U.S. assets for the yield-and-stability trade rotates out. A weaker dollar pushes import prices up — which pushes inflation up — which makes the original problem worse.</li>
          <li><strong>Inflation expectations un-anchor.</strong> Consumers and businesses start building expected inflation into wages and prices. Once that happens, it takes a recession to reverse. The Fed of the 1970s learned this. Volcker (1979-1987) had to engineer a brutal recession to undo the damage. Every Fed since has treated "anchored inflation expectations" as the prize worth defending.</li>
        </ol>

        <div class="example-box">
          <div class="label">What this means for Warsh's first six months</div>
          <p style="font-family: 'Fraunces', serif; font-size: 16px; line-height: 1.6; margin-bottom: 14px;">Warsh has spent decades inside the Fed system. He served as a Fed Governor from 2006-2011, including during the financial crisis. He knows exactly what happens to a central bank that loses credibility — he watched the European Central Bank live through it during the eurozone crisis.</p>

          <p style="font-family: 'Fraunces', serif; font-size: 16px; line-height: 1.6; margin-bottom: 14px;"><span class="confidence confidence-interp">Interp</span> The most likely scenario is the one the market currently underprices: Warsh holds rates, signals data dependence, and uses his first speeches to anchor expectations rather than ease conditions. That preserves Fed credibility — and disappoints the President who appointed him. The political fallout is a 2027 story, not a 2026 story.</p>

          <p style="font-family: 'Fraunces', serif; font-size: 16px; line-height: 1.6; margin-bottom: 0;"><span class="confidence confidence-speculation">Spec</span> The less likely but more consequential scenario: Warsh cuts in June or July despite the data. If he does, watch the 30-year Treasury yield. A move from ~4.8% to 5.2%+ within a week would be the market telling him the cut was a mistake. That's the moment the regime changes.</p>
        </div>

        <p style="margin-top: 24px;"><strong>What to do with this:</strong> Don't trade Fed personnel news. Trade Fed credibility. The right question after every Fed event isn't "did they cut?" — it's "what did the 30-year yield do?" If the long end rallies (yields fall) on a cut, the market trusts the move. If the long end sells off (yields rise) on a cut, the market is telling you the Fed just made things worse. Same action, opposite information.</p>

        <p>This is also why "the Fed will save us" is a more fragile assumption than it used to be. A Fed that cuts into hot inflation isn't a savior — it's a vandal in a Brooks Brothers suit. The market knows this. The financial press often doesn't.</p>
      `
    },

    {
      id: 'section-3',
      number: '§ 03',
      title: 'A move dissected',
      subtitle: 'Last week we framed this stock as the confirmation test. The test came back — and it confirmed the opposite of what bears expected.',
      body: `
        <div class="dissection-card">
          <div class="dissection-meta">
            <span><strong>Ticker:</strong> <span class="ticker" data-ticker="NBIS">NBIS</span></span>
            <span><strong>Company:</strong> Nebius Group</span>
            <span><strong>Move:</strong> <span class="move-indicator move-up">+18% to all-time high</span></span>
            <span><strong>Date:</strong> May 13, 2026</span>
          </div>

          <div class="dissection-step">
            <div class="dissection-step-label">Step 1 · The headline reason</div>
            <p style="margin-bottom: 0;">"Nebius crushes Q1 estimates, surges to all-time high on AI demand." This is what most financial media reported. <span class="confidence confidence-fact">Fact</span> Revenue of $399M vs. $379M expected. Adjusted EBITDA of $130M (32% margin) vs. a $54M loss in the same quarter last year. EPS of -$0.23 vs. -$0.78 expected. Stock to $213.</p>
          </div>

          <div class="dissection-step">
            <div class="dissection-step-label">Step 2 · What's underneath that headline</div>
            <p style="margin-bottom: 0;"><span class="confidence confidence-fact">Fact</span> Two numbers matter more than the revenue beat. First, Nebius AI EBITDA margin expanded from 24% in Q4 to <span class="data-callout">45% in Q1</span> — a 21-point jump in a single quarter. Second, the company announced a $27B five-year capacity contract with Meta ($12B dedicated compute plus a $15B option). <span class="confidence confidence-interp">Interp</span> The combination tells you two things at once: Nebius can scale revenue without losing margin, and demand for its capacity is still being signed in eleven-figure increments by the largest AI buyers in the world.</p>
          </div>

          <div class="dissection-step">
            <div class="dissection-step-label">Step 3 · The actual structural story (and why it matters)</div>
            <p style="margin-bottom: 0;"><span class="confidence confidence-interp">Interp</span> In Issue 2, we framed Nebius as the "confirmation test" for the AI infrastructure thesis. CoreWeave had just guided weakly and raised capex — the "first crack." The framework we offered: <em>if Nebius reports with strong revenue but weak operating leverage, the AI-cloud thesis cracks. If margins expand, the thesis lives.</em> Margins expanded — by 21 points. That's not a minor confirmation. It's a strong signal that the AI-infrastructure business model can scale into profit, not just revenue.</p>
          </div>

          <div class="dissection-step">
            <div class="dissection-step-label">Step 4 · What this means for sharp investors vs. retail investors</div>
            <p style="margin-bottom: 0;"><span class="confidence confidence-interp">Interp</span> A sharp investor reading this print did two things. First, they updated the AI-infra thesis upward — the "first crack" was idiosyncratic to CoreWeave's execution, not a sector-wide problem. Second, they immediately asked the follow-up question: <em>if Nebius can do 45% EBITDA margins, why is CoreWeave struggling to get to break-even?</em> That's the dispersion question that separates winners from losers within a hot sector. Same business model, very different execution.</p>

            <p style="margin-top: 14px; margin-bottom: 0;"><span class="confidence confidence-speculation">Spec</span> The retail-investor mistake here is to treat NBIS at $213 as "expensive" and CRWV at its recent lows as "cheap." The math doesn't work that way. A company growing 684% YoY at 32% group EBITDA margins is mispriced in either direction depending on where its growth lands. The honest answer is that NBIS's 2026 ARR target of $7-9B is what matters — if they hit the top end, today's price is reasonable; if they hit the bottom end, it's expensive; if they exceed it, $213 looks like a starting price.</p>
          </div>

          <div class="dissection-step">
            <div class="dissection-step-label">Step 5 · The lesson</div>
            <p style="margin-bottom: 0;">Patterns don't always confirm in the direction the bears expect. Two weeks ago, the AI-infrastructure thesis looked like it was developing its first real crack. The pattern we taught — "wait for the second name to confirm or deny the first" — is meant to be used in <em>both directions</em>. Nebius didn't confirm weakness; it confirmed strength. The honest investor updates accordingly. The bad investor stays attached to their previous read.</p>

            <p style="margin-top: 14px; margin-bottom: 0;">This is also why being humble about your own framework matters. We framed NBIS as a confirmation test for a bearish thesis. The test came back bullish. That doesn't mean the framework was wrong — it means the test resolved in the upside direction. Frameworks that can resolve either way are how investors learn. Frameworks that only confirm what you already believe are how investors lose money slowly.</p>
          </div>
        </div>

        <p style="font-style: italic; color: var(--ink-muted); font-size: 15px; margin-top: 24px;">The NVDA print Tuesday is the next major AI-infra data point. Watch data center revenue, China commentary, and forward guidance. If NVDA confirms what NBIS just signaled, the "AI capex is slowing" narrative dies for at least another quarter.</p>
      `
    },

    {
      id: 'section-4',
      number: '§ 04',
      title: 'Sectors that mattered',
      subtitle: 'Only the sectors where something genuinely happened. Equal coverage of every sector dilutes the signal.',
      body: `
        <h3 class="subsection-title">Energy</h3>
        <p class="subsection-tagline">Outperforming again — but now for the right reason. This is no longer just a geopolitics trade.</p>

        <p><span class="confidence confidence-fact">Fact</span> Energy was one of the leading sectors of the week. <span class="ticker" data-ticker="OXY">OXY</span> +2.8%, <span class="ticker" data-ticker="XOM">XOM</span> +2.2%, <span class="ticker" data-ticker="APA">APA</span> +1.8%, with the XLE sector ETF and XOP exploration ETF both up roughly in line. USO (the oil futures ETF) gained 2.2% on the week.</p>

        <p><span class="confidence confidence-interp">Interp</span> What changed: energy is no longer just rallying on Iran headlines. It's now also working as an inflation hedge. A 3.8% CPI print where energy was 40% of the increase tells you two things simultaneously — (1) oil prices are still elevated and feeding into the inflation story, and (2) energy companies' earnings are being directly boosted by exactly what's hurting consumers. That's a powerful combination. Energy equities are the rare asset class that benefits from <em>both</em> sticky inflation and geopolitical risk.</p>

        <div class="example-box">
          <div class="label">A subtle structural shift</div>
          <p style="margin-bottom: 0; font-family: 'Fraunces', serif; font-size: 16px; line-height: 1.6;">Through 2024 and most of 2025, energy was a "value trap" trade — cheap multiples but no catalyst. The combination of (a) elevated oil from sustained conflict, (b) inflation re-accelerating, and (c) the Fed unable to cut rates has converted energy from value trap into something closer to a defensive growth trade. <span class="confidence confidence-speculation">Spec</span> If May CPI confirms the April pattern, energy outperformance likely continues — but the day Iran resolves, these stocks give back 15-20% in a week. The setup remains asymmetric. Own it knowingly, not blindly.</p>
        </div>

        <hr style="border: none; border-top: 1px solid var(--rule); margin: 48px 0 32px;">

        <h3 class="subsection-title">Technology — AI Infrastructure</h3>
        <p class="subsection-tagline">The "first crack" thesis from last week didn't survive Nebius. The picks-and-shovels trade is alive.</p>

        <p><span class="confidence confidence-fact">Fact</span> <span class="ticker" data-ticker="NBIS">NBIS</span> hit an all-time high of $213 after Q1 (covered in detail in §03). <span class="ticker" data-ticker="MSFT">MSFT</span> was the week's largest mega-cap gainer at +2.8% on continued Azure AI growth. <span class="ticker" data-ticker="CSCO">CSCO</span> rose roughly 15% after Q1 results showed surging AI-driven orders alongside an announcement of approximately 4,000 layoffs.</p>

        <p><span class="confidence confidence-interp">Interp</span> The Cisco move is the most interesting tell of the week. Cisco — a slow-growth legacy networking company most investors had written off — was rewarded by the market for the exact same playbook now being run by Big Tech: lean into AI demand, cut headcount, expand margins. The market is rewarding <em>operating leverage from AI</em> regardless of the underlying business. That's a meaningful expansion of the AI trade beyond pure-play infrastructure and into the legacy enterprise tech that can be repositioned around it.</p>

        <p><strong>The key tell:</strong> NVDA reports Tuesday. If their data center segment hits the ~$73B expectation and they guide to continued strength in H2, the AI-capex-is-slowing narrative dies completely for the quarter. If they guide cautiously — especially on China — the narrative resurfaces. Either way, the print sets the tone for the AI complex through earnings season's end.</p>

        <hr style="border: none; border-top: 1px solid var(--rule); margin: 48px 0 32px;">

        <h3 class="subsection-title">Small-Caps</h3>
        <p class="subsection-tagline">The Great Rotation accelerated. The Russell 2000 is now up more than double the S&amp;P year-to-date.</p>

        <p><span class="confidence confidence-fact">Fact</span> Through mid-May, the Russell 2000 is up <span class="data-callout">16.3% YTD</span> versus the S&amp;P 500 up 7.6% and the Nasdaq Composite up 11.2%. The Russell hit a fresh record on May 6 at 2,886.77. The valuation gap between small-caps and the S&amp;P 500 has been closing not by mega-caps falling, but by small-caps rising.</p>

        <p><span class="confidence confidence-interp">Interp</span> We flagged this rotation as a developing story in Issue 2 — and it has only intensified. The drivers haven't changed: OBBBA tax provisions, broader earnings participation across sectors, and the unwinding of the extreme mega-cap concentration that defined 2023-2024. What's new this week: even with a hot CPI print and bond yields rising — both of which should have hurt small-caps more than large-caps — the Russell continued to hold up. That kind of relative strength against an unfavorable macro backdrop is the signature of a real rotation, not a fakeout.</p>

        <p><span class="confidence confidence-speculation">Spec</span> The historical analog remains 2000-2006, when small-caps significantly outperformed for years following a mega-cap unwind. Whether 2026 follows the same path is unknown, but the structural similarities — concentrated leadership unwinding, broader earnings participation, valuation gap normalizing — are getting harder to ignore.</p>

        <div class="quiet">
          <div class="quiet-title">Other sectors, briefly</div>
          <div class="quiet-item"><strong>Healthcare:</strong> Quiet week for the sector overall. <span class="ticker" data-ticker="OSCR">OSCR</span> (Oscar Health) ticked up 2% on a price-target raise. <span class="confidence confidence-interp">Interp</span> The thesis from Issue 2 — that tech-enabled health insurance is taking share from legacy — remains intact but slow-moving.</div>
          <div class="quiet-item"><strong>Consumer:</strong> Hims &amp; Hers fell 13% on weak guidance early in the week. On Holding beat with double-digit China growth. <span class="confidence confidence-interp">Interp</span> The bifurcation in consumer continues — premium and aspirational brands working, value-and-promotional names struggling. Walmart's print Wednesday is the next major data point.</div>
          <div class="quiet-item"><strong>International:</strong> Alibaba's core profit fell 84% as the CEO defended AI investment, while Tencent showed strength from gaming and AI demand despite revenue coming in light. <span class="confidence confidence-interp">Interp</span> The Chinese internet trade is now genuinely two stocks moving in opposite directions on the same underlying theme. SoftBank's Vision Fund posted a $46B gain driven primarily by its OpenAI position.</div>
          <div class="quiet-item"><strong>Financials:</strong> Mostly quiet, but watch closely. If long-end yields keep rising while short-end stays anchored, the steepener trade benefits banks materially. The current FOMC dissent dynamic argues for continued steepening.</div>
        </div>
      `
    },

    {
      id: 'section-5',
      number: '§ 05',
      title: 'Pattern recognition',
      subtitle: 'Markets repeat patterns more than they admit. This week reveals two of them — one on streaks, one on confirmation tests.',
      body: `
        <div class="kicker">This week's pattern</div>
        <div class="concept-callout">"Streaks break on the news that was already there." Six up weeks didn't end because something new happened. They ended because the market finally noticed what had been true all along.</div>

        <p>Going into Friday, the S&amp;P had risen for six consecutive weeks. Then it fell 1.24% in a single session. What changed on Friday that wasn't true on Thursday? Genuinely nothing. The Trump-Xi summit had already ended. The CPI print was three days old. Warsh had been confirmed. Friday's selloff wasn't caused by new information — it was caused by the market finally accepting old information.</p>

        <p><strong>The pattern:</strong> Markets rise on hope through accumulating signs of trouble. The trouble doesn't immediately register because positioning is light, sentiment is bullish, and dip-buyers are aggressive. Then on some Friday — usually before a long weekend or just after a meaningful technical level — the accumulated information catches up. The selloff isn't proportional to that day's news. It's proportional to the news of the last six weeks, repriced in one session.</p>

        <ul style="margin: 16px 0 16px 24px; font-family: 'Fraunces', serif; font-size: 16px; line-height: 1.65;">
          <li><strong>October 2018.</strong> S&amp;P 500 ran into early October hitting fresh highs despite rising yields and Fed hiking signals. Then one Wednesday it fell 3% and started a 20% drawdown. Nothing specific happened that Wednesday — markets just stopped ignoring what had been true for weeks.</li>
          <li><strong>February 2020.</strong> The S&amp;P hit all-time highs on February 19, 2020 — with COVID already a known issue, already spreading in Italy, already affecting Chinese factories. Then it fell 34% in five weeks. The information was there. The market just hadn't priced it.</li>
          <li><strong>September 2008.</strong> The Bear Stearns failure was in March. Markets didn't actually crash until September. Six months of accumulating evidence the system was breaking, ignored until it wasn't.</li>
        </ul>

        <p><span class="confidence confidence-interp">Interp</span> Friday's -1.24% isn't the start of a 2020-style event. It's a much more modest example of the same pattern: markets rose for six weeks on Q1 earnings momentum while quietly absorbing the worst inflation print in three years, a contentious Fed transition, and a disappointing summit. Friday was the day the accumulated overhang finally hit the tape.</p>

        <p><strong>The second pattern this week is the inverse of last week's.</strong> We taught the "first crack" pattern in Issue 2 — when one company in a hot theme misses, watch what the second company does. That pattern resolved this week, in the bullish direction. CoreWeave had been the first crack. Nebius was the confirmation test. Nebius confirmed strength, not weakness. The AI-infra thesis survived the test.</p>

        <p>This is the harder version of pattern recognition: <strong>patterns that can resolve in either direction are more reliable than patterns that only confirm what you expected.</strong> An investor who used the "first crack" pattern correctly didn't sell AI-infra two weeks ago — they waited for the second data point. The waiting was the discipline. The waiting paid.</p>

        <div class="positioning">
          <div class="positioning-label">How to use these patterns as an investor</div>
          <span class="confidence confidence-interp">Interp</span> Two takeaways. First: don't be surprised when a multi-week rally ends on a day with no specific catalyst. The catalyst is usually the accumulated weight of news the market had been ignoring. Second: when you frame a confirmation test in advance, commit to honoring the result in either direction. The discipline is in saying "if X happens, my thesis is wrong" — and then actually updating when X doesn't happen the way you expected. That's the part most investors skip.
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
          <div class="story-meta">Tracking since Issue #1 · Status: <span class="story-status status-confirmed">Test Resolved — Bullish</span></div>
          <p style="font-size: 16px;">The "first crack" thesis from Issue 2 has been tested and rejected. Nebius's Q1 print delivered a 21-point EBITDA margin expansion in a single quarter and a $27B Meta capacity contract. The bear case for AI-infra is now harder to make than it was a week ago. Next test: NVDA Tuesday.</p>
          <p class="story-progress">Movement since last issue: Significantly positive. Thesis intact, with the strongest data point of the cycle.</p>
        </div>

        <div class="story">
          <h3 class="story-title">Will the Fed cut rates in 2026?</h3>
          <div class="story-meta">Tracking since Issue #1 · Status: <span class="story-status status-cracking">Effectively Dead</span></div>
          <p style="font-size: 16px;">April CPI at 3.8% combined with the unusually contentious 8-4 April FOMC vote effectively killed rate-cut expectations for 2026. Market pricing has moved to a better-than-1-in-3 chance of a <em>hike</em> by year-end. The Warsh transition adds uncertainty but doesn't change the underlying inflation math.</p>
          <p class="story-progress">Movement since last issue: Sharply negative. The "Fed pivot" trade that anchored 2026 expectations has now reversed direction.</p>
        </div>

        <div class="story">
          <h3 class="story-title">The Great Rotation: small-caps over mega-caps</h3>
          <div class="story-meta">Tracking since Issue #2 · Status: <span class="story-status status-developing">Accelerating</span></div>
          <p style="font-size: 16px;">Russell 2000 now +16.3% YTD vs. S&amp;P +7.6%. The rotation continued holding up even through a hot CPI print that should have hurt rate-sensitive small-caps disproportionately. That relative strength is the signature of a real regime change, not a fakeout. The 2000-2006 historical analog remains the most relevant comparison.</p>
          <p class="story-progress">Movement since last issue: Positive. Rotation accelerated rather than faded.</p>
        </div>

        <div class="story">
          <h3 class="story-title">Will the Iran conflict resolve, and when?</h3>
          <div class="story-meta">Tracking since Issue #1 · Status: <span class="story-status status-watching">Watching</span></div>
          <p style="font-size: 16px;">No major new developments this week. Brent crude held above $100. Energy stocks outperformed as the conflict's contribution to inflation now feeds into the broader macro story. The conflict has now persisted longer than most historical geopolitical premium trades, and the elevated-oil baseline is increasingly being treated as structural rather than spiked.</p>
          <p class="story-progress">Movement since last issue: Neutral. No resolution catalysts on the calendar, no escalation. The "stuck" scenario is now the base case.</p>
        </div>

        <div class="story">
          <h3 class="story-title">US-China tariff structure: will it ease?</h3>
          <div class="story-meta">New this issue · Status: <span class="story-status status-watching">Active</span></div>
          <p style="font-size: 16px;">Added this week because the Beijing summit clarified — by its absence of substance — that the existing tariff regime is the operating reality, not a temporary state. The Boeing order and ag-purchase commitments don't change the underlying tariff math. For multinationals and China-exposed names (semis, industrials, consumer goods), this is now a sustained margin headwind, not a near-term resolution story.</p>
          <p class="story-progress">Movement since last issue: New tracking. Watching for any sign of tariff-relief catalysts (legislation, executive action, secondary summit) through summer.</p>
        </div>

        <div class="story">
          <h3 class="story-title">Fed independence under political pressure</h3>
          <div class="story-meta">New this issue · Status: <span class="story-status status-watching">Watching</span></div>
          <p style="font-size: 16px;">The 54-45 Warsh confirmation — the narrowest in Fed Chair history — combined with the 8-4 April FOMC dissent puts the question of Fed independence into the foreground for the first time since the early 1990s. <span class="confidence confidence-speculation">Spec</span> The first real test is the June 16-17 FOMC meeting. The medium-term test is whether the dollar and long-end yields start pricing in an "independence discount" that didn't exist before.</p>
          <p class="story-progress">Movement since last issue: New tracking. Will watch the 30-year Treasury yield, dollar index, and gold as the cleanest signals of how markets are scoring credibility.</p>
        </div>

        <div class="story">
          <h3 class="story-title">Is the K-shape consumer becoming permanent?</h3>
          <div class="story-meta">Tracking since Issue #1 · Status: <span class="story-status status-watching">Watching</span></div>
          <p style="font-size: 16px;">Hims &amp; Hers weak guidance and On Holding's China strength bracket the bifurcation. Walmart reports Wednesday — the cleanest single read on mainstream consumer behavior available. The K-shape continues to widen, but with more nuance than "premium up, value down" — execution within each tier matters as much as which tier you're in.</p>
          <p class="story-progress">Movement since last issue: Neutral. Awaiting Walmart and retail sales data this week.</p>
        </div>
      `
    },

    {
      id: 'section-7',
      number: '§ 07',
      title: 'Your toolkit',
      subtitle: 'Tool №03 this week. Over 52 weeks, this builds into a real framework for thinking about markets.',
      body: `
        <div class="tool">
          <div class="tool-number">TOOL № 03 · NEW THIS WEEK</div>
          <h3 class="tool-name">The CPI Decoder</h3>
          <p style="margin-bottom: 12px;">CPI reports get reported as one number — "inflation came in at 3.8%." That number alone tells you almost nothing useful. The actual signal is in the components. Here's how to read a CPI release in five minutes and understand what it actually means.</p>
          <ol>
            <li><strong>Headline vs. core.</strong> Headline includes food and energy. Core excludes them. Core is what the Fed actually targets, because energy and food bounce around for non-monetary reasons. If headline is high but core is moderating, the Fed has room to be patient. If core is high, the Fed has a real problem.</li>
            <li><strong>Year-over-year vs. month-over-month.</strong> YoY tells you the trend. MoM tells you what's happening right now. A high YoY with cooling MoM means inflation is rolling over. A low YoY with rising MoM means it's about to accelerate. April's print had both YoY (3.8%) and MoM (0.4%) trending up — a worst-case combination.</li>
            <li><strong>Energy contribution.</strong> If energy is doing most of the work (40% in April), the move is being driven by a single category that's exogenous to Fed policy. The Fed can't fight oil prices with rates. But energy that stays elevated <em>feeds into</em> everything else over the next 3-6 months — transport, food, manufacturing — and that <em>is</em> what the Fed reacts to.</li>
            <li><strong>Shelter.</strong> Shelter is roughly a third of CPI and lags actual housing data by ~12 months. If shelter is still rising in the print but real-time rent data is moderating, you can expect that to flow through CPI over the next year. Shelter's stickiness is why the Fed cares so much about getting it under control before declaring victory.</li>
            <li><strong>The market reaction within the first hour.</strong> Bond yields, the dollar, and gold all move within 30 seconds of the release. Watch which moves more. Yields up + dollar up = market thinks the Fed has to be more hawkish. Yields up + dollar down + gold up = market thinks inflation is winning and the Fed is losing credibility. The combination tells you the regime.</li>
          </ol>
          <div class="tool-meta">CPI drops monthly. Run this decoder for the next three prints in a row, and you'll have built a sharper mental model than 90% of retail investors.</div>
        </div>

        <div class="toolkit-history">
          <h4>Toolkit so far · The list grows each week</h4>
          <p>Tool № 01 — The Four Questions Before Buying Any Stock (Issue #1)</p>
          <p>Tool № 02 — The Earnings Reaction Decoder (Issue #2)</p>
          <p>Tool № 03 — The CPI Decoder (Issue #3)</p>
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
          <h3 class="news-headline">Wednesday, May 20 (after close): NVIDIA Q1 FY27 earnings</h3>
          <p class="news-body">The single most important market event of the week, and arguably the quarter. Consensus expects revenue of ~$78B (±2%) with data center revenue near $73B and non-GAAP EPS of $1.77. The most-watched items: data center growth rate, China commentary (assumed zero China data-center revenue currently), Blackwell product progression, and forward guidance for Q2.</p>
          <p class="news-body"><strong>What to learn:</strong> NVDA reports after the close. The first move is in after-hours, when liquidity is thin and reactions are loud. The <em>real</em> price discovery happens in the first hour of regular trading the next day. Compare the after-hours move to the open — if they agree, the print was clean. If they disagree (after-hours up, open down), professional money is fading retail's reaction. That divergence is information.</p>
        </div>

        <div class="news-item">
          <h3 class="news-headline">Thursday, May 21 (pre-market): Walmart Q1 FY27 earnings</h3>
          <p class="news-body">The cleanest single read on the U.S. consumer available. Consensus expects revenue ~$174.6B (+5.4%) and EPS of $0.66. The most-watched item: U.S. comparable store sales growth (consensus 3.9%) and any commentary on consumer trade-down trends. Advertising revenue (~$6.4B last quarter, growing 46% YoY) is also worth watching as the secondary growth engine.</p>
          <p class="news-body"><strong>What to learn:</strong> Walmart talks more bluntly about the actual U.S. consumer than almost any other public company. Read the prepared remarks <em>before</em> the financials. The qualitative language ("customers are stretching," "trade-down is accelerating," "demand for staples is firming") tells you what's actually happening in households — which is upstream of every consumer-related stock you own.</p>
        </div>

        <div class="news-item">
          <h3 class="news-headline">Wednesday, May 20: April FOMC minutes</h3>
          <p class="news-body">The detailed record of the April meeting where four members dissented — the most contentious vote since 1992. The market wants to know: were the dissents about tactics (timing of cuts) or strategy (whether cutting at all is appropriate)? The minutes will reveal which.</p>
          <p class="news-body"><strong>What to learn:</strong> FOMC minutes are released three weeks after the meeting itself. By the time they're public, much of the substance has been telegraphed. What still matters: the specific language used to describe inflation risk. "Persistent," "uncomfortable," "concerning" are hawkish signal words. "Transitory," "easing," "moderating" are dovish. Count which side dominates.</p>
        </div>

        <div class="news-item">
          <h3 class="news-headline">Any first public remarks from Chair Warsh</h3>
          <p class="news-body">Warsh took office May 15. His first public remarks as Chair will move markets disproportionately to the actual content, because every word will be parsed for direction. Watch for: (1) does he use "data dependence" language similar to Powell? (2) does he reference the 2% target by name? (3) does he address Fed independence directly? Any answer is informative; silence on any of these is also informative.</p>
          <p class="news-body"><strong>What to learn:</strong> First Fed Chair speeches are theater more than policy, but the theater is what markets price first. Watch the 30-year Treasury yield and the dollar index during the speech itself. Real-time market reaction to Fed-speak tells you what the smart money thinks the speech meant — usually before any financial pundit has parsed it.</p>
        </div>
      `
    }
  ]
});
