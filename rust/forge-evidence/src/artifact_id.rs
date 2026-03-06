use crate::hash::sha256_hex;

pub fn artifact_id_hex(kind: &str, canonical_content: &[u8]) -> String {
    let mut payload = Vec::with_capacity(kind.len() + canonical_content.len() + 1);
    payload.extend_from_slice(kind.as_bytes());
    payload.push(0);
    payload.extend_from_slice(canonical_content);
    sha256_hex(&payload)
}

#[cfg(test)]
mod tests {
    use super::artifact_id_hex;

    #[test]
    fn artifact_id_is_stable() {
        let canonical = br#"{"a":1,"b":2}"#;
        let one = artifact_id_hex("risk_heatmap", canonical);
        let two = artifact_id_hex("risk_heatmap", canonical);
        assert_eq!(one, two);
        assert_eq!(one.len(), 64);
    }
}
