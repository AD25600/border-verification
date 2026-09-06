"""
Synthetic dataset generator matching the REAL feature dict produced by
VerificationPipelineService._build_feature_vector (7 keys, some nullable):

    document_type_confidence     float | None   [0,1]
    ocr_average_confidence       float | None   [0,1]
    ocr_field_count              int            >=0
    mrz_all_checksums_valid      bool  | None
    mrz_checksum_failure_count   int   | None   >=0
    tampering_anomaly_score      float | None   [0,1]  (0=clean, 1=tampered)
    tampering_indicator_count    int            >=0

No real pipeline logs were available, so this generator encodes realistic
causal structure + noise + missingness so metrics are meaningful for THIS
synthetic distribution. Replace with real logs before production use.
"""
import numpy as np
import pandas as pd

SEED = 42
N = 12000
POSITIVE_RATE = 0.80  # 80% VERIFIED(1) / 20% REJECTED(0)


def generate(n=N, seed=SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n_pos = int(n * POSITIVE_RATE)
    labels = np.array([1] * n_pos + [0] * (n - n_pos))
    rng.shuffle(labels)

    rows = []
    for label in labels:
        if label == 1:
            doc_conf = np.clip(rng.normal(0.95, 0.04), 0, 1)
            ocr_conf = np.clip(rng.normal(0.93, 0.05), 0, 1)
            ocr_count = int(np.clip(rng.normal(9, 1), 4, 12))
            checksum_fail = rng.choice([0, 1], p=[0.96, 0.04])
            mrz_valid = checksum_fail == 0
            tamper = np.clip(rng.beta(1.2, 25), 0, 1)
            tamper_ind_count = int(rng.poisson(0.2))
        else:
            profile = rng.choice(["mrz", "tamper", "ocr", "mixed"], p=[0.3, 0.3, 0.2, 0.2])
            doc_conf = np.clip(rng.normal(0.8 if profile != "ocr" else 0.6, 0.15), 0, 1)
            ocr_conf = np.clip(rng.normal(0.6 if profile in ("ocr", "mixed") else 0.8, 0.15), 0, 1)
            ocr_count = int(np.clip(rng.normal(6, 2), 0, 12))
            fail_p = 0.7 if profile in ("mrz", "mixed") else 0.15
            checksum_fail = rng.poisson(1.5) if rng.random() < fail_p else 0
            mrz_valid = checksum_fail == 0
            tamper_p = 0.7 if profile in ("tamper", "mixed") else 0.2
            tamper = np.clip(rng.beta(6, 3) if rng.random() < tamper_p else rng.beta(1.5, 15), 0, 1)
            tamper_ind_count = int(rng.poisson(2.5 if profile in ("tamper", "mixed") else 0.4))

        rows.append(
            dict(
                document_type_confidence=float(doc_conf),
                ocr_average_confidence=float(ocr_conf),
                ocr_field_count=int(ocr_count),
                mrz_all_checksums_valid=bool(mrz_valid),
                mrz_checksum_failure_count=int(checksum_fail),
                tampering_anomaly_score=float(tamper),
                tampering_indicator_count=int(tamper_ind_count),
                label=int(label),
            )
        )

    df = pd.DataFrame(rows)

    # Inject missingness matching real pipeline stage failures: a whole stage
    # being SKIPPED/FAILED/NOT_CONFIGURED means its fields arrive as None.
    miss_rng = np.random.default_rng(seed + 1)
    detection_missing = miss_rng.random(len(df)) < 0.03
    df.loc[detection_missing, "document_type_confidence"] = np.nan

    ocr_missing = miss_rng.random(len(df)) < 0.03
    df.loc[ocr_missing, "ocr_average_confidence"] = np.nan

    mrz_missing = miss_rng.random(len(df)) < 0.08  # MRZ stage is SKIPPED whenever no mrz_zone found
    df["mrz_all_checksums_valid"] = df["mrz_all_checksums_valid"].astype(object)
    df.loc[mrz_missing, "mrz_all_checksums_valid"] = None
    df.loc[mrz_missing, "mrz_checksum_failure_count"] = np.nan

    tampering_missing = miss_rng.random(len(df)) < 0.03
    df.loc[tampering_missing, "tampering_anomaly_score"] = np.nan

    return df.sample(frac=1.0, random_state=seed).reset_index(drop=True)


if __name__ == "__main__":
    df = generate()
    df.to_csv("data/synthetic_dataset.csv", index=False)
    print(df["label"].value_counts(normalize=True))
