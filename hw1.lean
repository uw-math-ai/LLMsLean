--Math 480, Spring 2025, Jarod Alper
--Homework 1: Fill in the sorries below
import Mathlib.Tactic
--Helpful tactics: rfl, rintro, use, rw, intro, exact, apply, triv, exfalso, left, right, cases'

-- 12
example : (P → Q → R) → P ∧ Q → R := by
  intro hPQR
  intro hPQ
  have hP := hPQ
  apply And.left at hPQ
  apply And.right at hP
  apply hPQR at hPQ
  apply hPQ at hP
  exact hP
