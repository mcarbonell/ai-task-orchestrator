---
id: T-XXX
title: "Task Title"
status: pending
priority: medium
dependencies: []
estimated_time: "2h"
---

## Description
Describe the functionality to be implemented here. Be specific about what is expected to be achieved.

## Acceptance Criteria
- [ ] [Specific and measurable criterion 1]
- [ ] [Specific and measurable criterion 2]
- [ ] [Specific and measurable criterion 3]

## Unit Tests
```bash
# Command to run specific tests for this task
npm test src/components/MyComponent.test.tsx
```

## E2E Tests (CDP)
```yaml
steps:
  - action: navigate
    url: http://localhost:3000/test-route
  
  - action: screenshot
    filename: step-1-initial.png
    width: 1280
    height: 720
  
  - action: eval
    code: |
      // Interact with the page
      document.querySelector('#input-field').value = 'test';
      document.querySelector('#submit-button').click();
  
  - action: wait
    milliseconds: 1000
  
  - action: screenshot
    filename: step-2-after-interaction.png
  
  - action: eval
    code: window.location.pathname
    expect: /expected-route

console_checks:
  - no_errors: true
  - allowed_warnings: ["React.StrictMode"]

performance_thresholds:
  lcp: 2500  # ms
  cls: 0.1
  fcp: 1800  # ms
  ttfb: 800  # ms
```

## Definition of Done
- [ ] All acceptance criteria met
- [ ] Unit tests pass (coverage > 80%)
- [ ] Screenshots generated and visually validated
- [ ] Browser console free of errors
- [ ] Performance metrics within thresholds
- [ ] Code follows project conventions

## Additional Notes
- [Relevant additional information]
- [Documentation links]
- [Special considerations]
