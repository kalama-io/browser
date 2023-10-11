import argparse
import base64
import hashlib
import json
import os
import subprocess
import sys
import zipfile


def generate_rsa(args):
    # `openssl genrsa 2048 | openssl pkcs8 -topk8 -nocrypt -out key.pem
    bin = args.bin if args.bin else 'openssl'
    out = args.out if args.out else 'key.pem'
    cmd = bin + ' genrsa 2048 | openssl pkcs8 -topk8 -nocrypt -out ' + out
    subprocess.call(cmd, shell=True)


def get_public_key(args):
    print(_get_public_key(args.pem_file, args.bin))


def _get_public_key(pem_file, bin):
    # `openssl rsa -in key.pem -pubout -outform DER | openssl base64 -A`
    assert os.path.exists(pem_file)
    bin = bin if bin else 'openssl'
    cmd = '%s rsa -in %s -pubout -outform DER' % (bin, pem_file)
    out_bytes = subprocess.check_output(cmd, shell=True).strip()
    return base64.b64encode(out_bytes).decode('utf-8')


def get_component_id(args):
    _get_component_id(args.pem_file, args.bin)


def _get_component_id(pem_file, bin):
    ## 'openssl rsa -in key.pem -pubout -outform DER | shasum -a 256 | head -c32 | tr 0-9a-f a-p'
    assert os.path.exists(pem_file)
    bin = bin if bin else 'openssl'
    cmd = '%s rsa -in %s -pubout -outform DER' % (bin, pem_file)
    out_bytes = subprocess.check_output(cmd, shell=True).strip()
    m = hashlib.sha256()
    m.update(bytes(out_bytes))
    component_id = ''.join([chr(int(i, base=16) + ord('a')) for i in m.hexdigest()][:32])
    print('component id = %s' % component_id)
    hash_string = hashlib.sha256(component_id.encode('utf-8')).hexdigest()
    print('component id hash = %s' % hash_string)

    data_public_key_sha2256 = []
    for i in range(0, len(hash_string), 2):
        data_public_key_sha2256.append('0x%s' % hash_string[i:i + 2])
    print('public key sha2256 = %s' % data_public_key_sha2256)


def pack_component(args):
    _pack_component(args.pem_file, args.pack_dir, args.bin, args.pack_zip)


def _unzip(zip_file, out_dir):
    with zipfile.ZipFile(zip_file) as f:
        for file_ in f.namelist():
            f.extract(file_, out_dir)


def _check_or_update_key(pem_file, manifest_content, manifest_file):
    pem_key = _get_public_key(pem_file, None)
    if 'key' in manifest_content:
        last_key = manifest_content['key']
        print('key %s found in  %s' % (last_key, manifest_file))
        assert last_key == pem_key, '%s is not equal %s' % (last_key, pem_key)
    else:
        manifest_content['key'] = pem_key
        print('Set keyword key value %s ' % pem_key)

    with open(manifest_file, mode='w', encoding='utf-8') as f:
        json.dump(manifest_content, f, indent=4)


def _pack_component(pem_file, pack_dir, bin, pack_zip):
    if pack_zip is not None and os.path.exists(pack_zip):
        if os.path.exists(pack_dir):
            os.remove(pack_dir)
        _unzip(pack_zip, pack_dir)
    assert os.path.exists(pack_dir), '%s does not exist' % pack_dir

    ## crx文件名同打包路径名
    out_crx_file = os.path.join(os.path.dirname(pack_dir), os.path.basename(pack_dir) + '.crx')
    if os.path.exists(out_crx_file):
        os.remove(out_crx_file)

    manifest_file = os.path.join(pack_dir, 'manifest.json')
    assert os.path.exists(manifest_file), ' %s does not exist' % manifest_file
    with open(manifest_file, mode='r', encoding='utf-8') as f:
        manifest_content = json.load(f)
    assert 'version' in manifest_content, '%s has no keyword: version' % manifest_content
    version = manifest_content['version']
    print('Pack conpomnet version = %s' % version)

    _check_or_update_key(pem_file, manifest_content, manifest_file)

    assert 'key' in manifest_content, '%s has no keyword: key' % manifest_content

    ## "C:\\Program Files\\Google\\Chrome\\Application"
    os.chdir(os.path.dirname(bin))

    assert os.path.exists(pem_file), '%s does not exist' % pem_file
    assert os.path.exists(pack_dir), '%s does not exist' % pack_dir
    pack_dir = os.path.abspath(pack_dir)
    pem_file = os.path.abspath(pem_file)

    ## 'chrome.exe --pack-extension=C:\myext --pack-extension-key=C:\myext.pem'
    cmd = os.path.basename(bin) + ' --pack-extension=%s --pack-extension-key=%s ' % (pack_dir, pem_file)
    print(cmd)

    job = subprocess.run(cmd, shell=True)
    if job.returncode != 0:
        print(job.returncode)
        return job.returncode
    if os.path.exists(out_crx_file):
        print('pack crx %s ' % out_crx_file)


def main(args):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help')

    group1 = subparsers.add_parser('generate_rsa')
    group1.add_argument('--out', help='out path')
    group1.add_argument('--bin', help='bin path')
    group1.set_defaults(func=generate_rsa)

    group2 = subparsers.add_parser('get_public_key')
    group2.add_argument('--pem-file', help='pem file path', required=True)
    group2.add_argument('--bin', help='bin path')
    group2.set_defaults(func=get_public_key)

    group3 = subparsers.add_parser('get_component_id')
    group3.add_argument('--pem-file', help='pem file path', required=True)
    group3.add_argument('--bin', help='bin path')
    group3.set_defaults(func=get_component_id)

    group4 = subparsers.add_parser('pack_component')
    group4.add_argument('--pem-file', help='pem file path', required=True)
    group4.add_argument('--bin', help='pack bin path, like chrome', required=True)
    group4.add_argument('--pack-dir', help='pack dir path', required=True)
    group4.add_argument('--pack-zip', help='pack zip path')
    group4.set_defaults(func=pack_component)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
