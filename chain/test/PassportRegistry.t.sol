// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {PassportRegistry} from "../src/PassportRegistry.sol";

interface Vm {
    function prank(address) external;
    function expectRevert(bytes calldata) external;
    function warp(uint256) external;
}

contract PassportRegistryTest {
    Vm constant vm = Vm(address(uint160(uint256(keccak256("hevm cheat code")))));
    PassportRegistry reg;
    address issuer = address(0xB7);
    bytes32 constant PID = keccak256("BTU-AI-2026-00001");

    function setUp() public {
        reg = new PassportRegistry();
        reg.setIssuer(issuer, true);
        vm.warp(1_760_000_000);
    }

    function _assert(bool ok, string memory msg_) internal pure {
        require(ok, msg_);
    }

    function testAnchorSequential() public {
        vm.prank(issuer);
        reg.anchorVersion(PID, 1, keccak256("v1"), keccak256("code1"));
        vm.prank(issuer);
        reg.anchorVersion(PID, 2, keccak256("v2"), keccak256("code2"));
        (uint32 v, PassportRegistry.VersionRecord memory r) = reg.getLatest(PID);
        _assert(v == 2, "latest");
        _assert(r.pdfHash == keccak256("v2"), "hash");
        _assert(r.issuer == issuer, "issuer");
    }

    function testOutOfOrderReverts() public {
        vm.prank(issuer);
        vm.expectRevert(abi.encodeWithSelector(PassportRegistry.VersionOutOfOrder.selector, uint32(1)));
        reg.anchorVersion(PID, 2, keccak256("v2"), keccak256("c"));
    }

    function testDuplicatePdfHashReverts() public {
        vm.prank(issuer);
        reg.anchorVersion(PID, 1, keccak256("same"), keccak256("c1"));
        vm.prank(issuer);
        vm.expectRevert(abi.encodeWithSelector(PassportRegistry.PdfHashReused.selector));
        reg.anchorVersion(PID, 2, keccak256("same"), keccak256("c2"));
    }

    function testNonIssuerReverts() public {
        vm.prank(address(0xBAD));
        vm.expectRevert(abi.encodeWithSelector(PassportRegistry.NotIssuer.selector));
        reg.anchorVersion(PID, 1, keccak256("v1"), keccak256("c"));
    }

    function testRevoke() public {
        vm.prank(issuer);
        reg.anchorVersion(PID, 1, keccak256("v1"), keccak256("c"));
        vm.prank(issuer);
        reg.revoke(PID, 1, "issued in error");
        PassportRegistry.VersionRecord memory r = reg.getVersion(PID, 1);
        _assert(r.revokedAt != 0, "revoked");
        vm.prank(issuer);
        vm.expectRevert(abi.encodeWithSelector(PassportRegistry.AlreadyRevoked.selector));
        reg.revoke(PID, 1, "again");
    }

    function testLookupPdf() public {
        vm.prank(issuer);
        reg.anchorVersion(PID, 1, keccak256("v1"), keccak256("c"));
        (bytes32 pid, uint32 v,) = reg.lookupPdf(keccak256("v1"));
        _assert(pid == PID && v == 1, "lookup");
        (bytes32 none,,) = reg.lookupPdf(keccak256("tampered"));
        _assert(none == bytes32(0), "tampered not found");
    }

    function testOnlyOwnerSetsIssuer() public {
        vm.prank(address(0xBAD));
        vm.expectRevert(abi.encodeWithSelector(PassportRegistry.NotOwner.selector));
        reg.setIssuer(address(0xBAD), true);
    }
}
