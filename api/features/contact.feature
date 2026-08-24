Feature: Contact form
  As a site visitor, I want to send a message to Steven directly, so I can
  start a real conversation outside the AI consultants.

  Scenario: Submitting a complete contact form
    When a visitor submits a complete contact form
    Then the contact submission is saved

  Scenario: Submitting an incomplete contact form
    When a visitor submits an incomplete contact form
    Then the contact submission is rejected
