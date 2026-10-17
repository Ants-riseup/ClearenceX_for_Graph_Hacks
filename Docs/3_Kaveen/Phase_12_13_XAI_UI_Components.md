# Phase 12 & 13 — XAI UI Components (Optional)

> **Priority:** SHOULD (Kaveen's Phase 10 already includes these inline)
> **Estimated Time:** 2–3 hours total (only if Kaveen needs separate components)
> **Dependencies:** Phase 06 (reasoning chains), Phase 08 (counterfactuals)

---

## Status: ⚠️ MAY BE SKIPPED

> [!IMPORTANT]
> **Kaveen's `DiscrepancyList.tsx` (Phase 10) already includes inline implementations of both the Reasoning Chain viewer and Counterfactual Cards.** Check with Kaveen — if his inline versions work, skip this phase entirely and focus your time on Phase 14 (API integration) instead.

---

## If Kaveen Wants Separate Components

### Phase 12 — ReasoningChainPanel

```tsx
// frontend/src/components/ReasoningChainPanel.tsx
import React, { useState } from 'react';

interface Props {
  chain: { steps: string[]; conclusion: string };
  isExpanded?: boolean;
}

export const ReasoningChainPanel: React.FC<Props> = ({ chain, isExpanded = false }) => {
  const [expanded, setExpanded] = useState(isExpanded);
  
  return (
    <div className="reasoning-chain">
      <button onClick={() => setExpanded(!expanded)} className="chain-toggle">
        🔗 Reasoning Chain ({chain.steps.length} steps)
        <span>{expanded ? '▼' : '▶'}</span>
      </button>
      
      {expanded && (
        <div className="chain-steps">
          {chain.steps.map((step, i) => (
            <div key={i} className={`chain-step ${step.includes('✓') ? 'pass' : step.includes('⚠') ? 'warn' : ''}`}>
              <span className="step-number">{i + 1}</span>
              <span className="step-text">{step}</span>
            </div>
          ))}
          <div className="chain-conclusion">
            <strong>Conclusion:</strong> {chain.conclusion}
          </div>
        </div>
      )}
    </div>
  );
};
```

### Phase 13 — CounterfactualCards

```tsx
// frontend/src/components/CounterfactualCards.tsx
import React from 'react';

interface Props {
  counterfactual: { options: string[]; recommendation: string };
}

export const CounterfactualCards: React.FC<Props> = ({ counterfactual }) => (
  <div className="counterfactual-section">
    <h4>💡 What would resolve this?</h4>
    <div className="cf-options">
      {counterfactual.options.map((option, i) => (
        <div key={i} className="cf-card">
          <span className="cf-icon">→</span>
          <span>{option}</span>
        </div>
      ))}
    </div>
    <div className="cf-recommendation">
      <strong>📋 Recommendation:</strong> {counterfactual.recommendation}
    </div>
  </div>
);
```

## Acceptance Criteria (if built)

- [ ] ReasoningChainPanel: expandable, numbered steps, color-coded (pass/warn)
- [ ] CounterfactualCards: shows options list + domain recommendation
- [ ] Both receive data from Aloka's backend format
- [ ] CSS matches Kaveen's design system
