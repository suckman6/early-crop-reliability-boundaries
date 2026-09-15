import importlib.util
import unittest


TORCH_AVAILABLE = importlib.util.find_spec("torch") is not None


@unittest.skipUnless(TORCH_AVAILABLE, "training PyTorch is isolated from the test environment")
class PrefixReliabilityLossTests(unittest.TestCase):
    def test_class_weights_are_normalized_on_training_samples(self):
        import torch

        from rcecrop.prefix_reliability_loss import inverse_sqrt_class_weights

        targets = torch.tensor([0, 0, 0, 1])
        weights = inverse_sqrt_class_weights(torch, targets, 2)
        self.assertGreater(float(weights[1]), float(weights[0]))
        self.assertAlmostEqual(float(weights[targets].mean()), 1.0, places=6)

    def test_missing_smoke_classes_are_ignored_without_changing_observed_weights(self):
        import torch

        from rcecrop.prefix_reliability_loss import inverse_sqrt_class_weights

        targets = torch.tensor([0, 0, 2])
        weights = inverse_sqrt_class_weights(torch, targets, 4)
        self.assertEqual(float(weights[1]), 0.0)
        self.assertEqual(float(weights[3]), 0.0)
        self.assertAlmostEqual(float(weights[targets].mean()), 1.0, places=6)

    def test_loss_is_finite_and_future_padded_values_do_not_change_it(self):
        import torch

        from rcecrop.prefix_reliability_loss import prefix_reliability_loss

        log_probs = torch.log(torch.tensor([[[0.7, 0.3], [0.8, 0.2]]]))
        stop = torch.tensor([[0.2, 0.9]])
        target = torch.tensor([0])
        valid = torch.tensor([[True, True]])
        times = torch.tensor([[10, 20]])
        quality = torch.tensor([[False, True]])
        weights = torch.tensor([1.0, 1.0])
        kwargs = dict(
            season_days=365,
            alpha=0.5,
            epsilon=1.0,
            prefix_cross_entropy_weight=0.25,
            consistency_weight=0.25,
            early_prefix_emphasis=1.0,
            minimum_quality_weight=0.25,
        )
        original, parts = prefix_reliability_loss(
            log_probs, stop, target, valid, times, quality, weights, **kwargs
        )
        padded, _ = prefix_reliability_loss(
            torch.cat([log_probs, torch.log(torch.tensor([[[0.01, 0.99]]]))], 1),
            torch.cat([stop, torch.tensor([[0.99]])], 1),
            target,
            torch.tensor([[True, True, False]]),
            torch.tensor([[10, 20, 364]]),
            torch.tensor([[False, True, False]]),
            weights,
            **kwargs,
        )
        self.assertTrue(torch.isfinite(original))
        self.assertTrue(torch.isfinite(parts["consistency_loss"]))
        self.assertAlmostEqual(float(original), float(padded), places=6)


if __name__ == "__main__":
    unittest.main()
