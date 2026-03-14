import os

def main():
    test_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Generate 500 Target Reqs (HLRs)
    target_path = os.path.join(test_dir, 'target_reqs.csv')
    with open(target_path, 'w') as f:
        f.write("ID,Description,Category\n")
        for i in range(1, 501):
            f.write(f"HLR-{i:04d},High Level Requirement {i},System\n")

    # 2. Generate 2000 Source Traces (LLRs)
    source_path = os.path.join(test_dir, 'source_reqs.csv')
    with open(source_path, 'w') as f:
        f.write("ID,Description,Parent_HLR\n")

        # Valid traces mapping to HLR 1-450 (4 items per HLR = 1800 valid traces)
        # This leaves HLR 451-500 missing (50 missing reqs)
        for hlr_id in range(1, 451):
            for j in range(4):
                llr_id = (hlr_id - 1) * 4 + j + 1
                f.write(f"LLR-{llr_id:04d},Sub-requirement {llr_id},HLR-{hlr_id:04d}\n")

        # Orphaned traces (mapping to non-existent HLRs 501-510)
        # 10 orphaned traces
        for i in range(10):
            llr_id = 1800 + i + 1
            f.write(f"LLR-{llr_id:04d},Orphaned sub-requirement,HLR-{500 + i + 1:04d}\n")

        # Invalid traces (15 items)
        for i in range(15):
             llr_id = 1810 + i + 1
             f.write(f"LLR-{llr_id:04d},Invalid parent format,HLR_INVALID_{i}\n")

    # 3. Write Config
    config_path = os.path.join(test_dir, 'custom_rules.yaml')
    with open(config_path, 'w') as f:
        f.write('''regex_rules:
  id_pattern: '^(HLR|LLR)-\\d{4}$'
columns:
  id: "ID"
  description: "Description"
  category: "Category"
tags:
  start_token: "["
  end_token: "]"
parser_settings:
  ignore_prefix: ""
''')

    print("Extreme Document Trace test data generated.")

if __name__ == '__main__':
    main()
