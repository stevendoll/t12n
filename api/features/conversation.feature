Feature: Visitor conversation with AI consultants
  As a site visitor, I want to start from an icebreaker and get replies from
  both Alex and Jamie, so the conversation reads like the real product does.

  Scenario: An active icebreaker is available
    Given an active icebreaker "The gap between knowing and doing is costing us."
    When a visitor requests an icebreaker
    Then the response is the active icebreaker

  Scenario: No active icebreakers are configured
    Given no active icebreakers exist
    When a visitor requests an icebreaker
    Then the icebreaker request fails with a 404

  Scenario: A visitor's first message gets two consultant replies
    Given an empty conversation
    When the visitor sends "We've talked about AI for two years. What's different now?"
    Then the turn is saved
    And two consultant replies are returned, from Alex and Jamie
