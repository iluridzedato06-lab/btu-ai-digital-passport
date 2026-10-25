// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title BTU AI Skills Digital Passport registry
/// @notice Anchors the SHA-256 hash of every officially issued passport version.
///         Only addresses authorised by the owner (Business and Technology University)
///         can anchor or revoke. Anyone can read.
contract PassportRegistry {
    struct VersionRecord {
        bytes32 pdfHash;   // sha256 of the exact PDF bytes
        bytes32 codeHash;  // sha256 of the verification code printed on the PDF
        uint64 issuedAt;   // block timestamp at anchoring
        uint64 revokedAt;  // 0 when not revoked
        address issuer;    // msg.sender that anchored the version
    }

    string public constant ISSUER_NAME = "Business and Technology University";
    string public constant ISSUER_DOMAIN = "btu.edu.ge";

    address public owner;
    address public pendingOwner;

    mapping(address => bool) public isIssuer;
    mapping(bytes32 => uint32) public latestVersion;
    mapping(bytes32 => mapping(uint32 => VersionRecord)) private records;
    mapping(bytes32 => bytes32) public passportByPdfHash;
    mapping(bytes32 => uint32) public versionByPdfHash;

    event OwnershipTransferStarted(address indexed previousOwner, address indexed newOwner);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    event IssuerSet(address indexed issuer, bool allowed);
    event VersionAnchored(
        bytes32 indexed passportIdHash,
        uint32 indexed version,
        bytes32 pdfHash,
        bytes32 codeHash,
        address indexed issuer,
        uint64 issuedAt
    );
    event VersionRevoked(bytes32 indexed passportIdHash, uint32 indexed version, address indexed by, string reason);

    error NotOwner();
    error NotPendingOwner();
    error NotIssuer();
    error VersionOutOfOrder(uint32 expected);
    error PdfHashReused();
    error UnknownVersion();
    error AlreadyRevoked();
    error ZeroValue();

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    modifier onlyIssuer() {
        if (!isIssuer[msg.sender]) revert NotIssuer();
        _;
    }

    constructor() {
        owner = msg.sender;
        emit OwnershipTransferred(address(0), msg.sender);
    }

    function transferOwnership(address newOwner) external onlyOwner {
        pendingOwner = newOwner;
        emit OwnershipTransferStarted(owner, newOwner);
    }

    function acceptOwnership() external {
        if (msg.sender != pendingOwner) revert NotPendingOwner();
        emit OwnershipTransferred(owner, msg.sender);
        owner = msg.sender;
        pendingOwner = address(0);
    }

    function setIssuer(address issuer, bool allowed) external onlyOwner {
        isIssuer[issuer] = allowed;
        emit IssuerSet(issuer, allowed);
    }

    function anchorVersion(bytes32 passportIdHash, uint32 version, bytes32 pdfHash, bytes32 codeHash)
        external
        onlyIssuer
    {
        if (passportIdHash == bytes32(0) || pdfHash == bytes32(0) || codeHash == bytes32(0)) revert ZeroValue();
        uint32 expected = latestVersion[passportIdHash] + 1;
        if (version != expected) revert VersionOutOfOrder(expected);
        if (passportByPdfHash[pdfHash] != bytes32(0)) revert PdfHashReused();

        uint64 ts = uint64(block.timestamp);
        records[passportIdHash][version] = VersionRecord(pdfHash, codeHash, ts, 0, msg.sender);
        latestVersion[passportIdHash] = version;
        passportByPdfHash[pdfHash] = passportIdHash;
        versionByPdfHash[pdfHash] = version;
        emit VersionAnchored(passportIdHash, version, pdfHash, codeHash, msg.sender, ts);
    }

    function revoke(bytes32 passportIdHash, uint32 version, string calldata reason) external onlyIssuer {
        VersionRecord storage r = records[passportIdHash][version];
        if (r.issuedAt == 0) revert UnknownVersion();
        if (r.revokedAt != 0) revert AlreadyRevoked();
        r.revokedAt = uint64(block.timestamp);
        emit VersionRevoked(passportIdHash, version, msg.sender, reason);
    }

    function getVersion(bytes32 passportIdHash, uint32 version) external view returns (VersionRecord memory) {
        return records[passportIdHash][version];
    }

    function getLatest(bytes32 passportIdHash) external view returns (uint32 version, VersionRecord memory record) {
        version = latestVersion[passportIdHash];
        record = records[passportIdHash][version];
    }

    function lookupPdf(bytes32 pdfHash)
        external
        view
        returns (bytes32 passportIdHash, uint32 version, VersionRecord memory record)
    {
        passportIdHash = passportByPdfHash[pdfHash];
        version = versionByPdfHash[pdfHash];
        record = records[passportIdHash][version];
    }
}
