// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title VoteValidator
 * @dev Smart contract for validating mesh network votes both on-chain and off-chain
 * Supports decentralized voting consensus with cryptographic verification
 */
contract VoteValidator {

    // Events
    event VoteRecorded(bytes32 indexed voteId, address indexed voter, bytes32 sessionId, uint256 timestamp);
    event SessionValidated(bytes32 indexed sessionId, ValidationResult result, uint256 totalVotes);
    event ConsensusReached(bytes32 indexed sessionId, bytes32 winningOption, uint256 consensusPercentage);

    // Enums
    enum ValidationResult { PENDING, VALID, INVALID, TIED }
    enum VoteType { ON_CHAIN, OFF_CHAIN_VERIFIED, OFF_CHAIN_PENDING }

    // Structs
    struct Vote {
        bytes32 voteId;
        address voter;
        bytes32 sessionId;
        bytes32 optionId;
        uint256 timestamp;
        VoteType voteType;
        bytes signature; // For off-chain verification
        bool isValid;
    }

    struct VotingSession {
        bytes32 sessionId;
        address creator;
        string title;
        bytes32[] options;
        uint256 startTime;
        uint256 endTime;
        uint256 minParticipants;
        uint256 consensusThreshold; // Percentage (0-100)
        ValidationResult status;
        mapping(bytes32 => uint256) voteCounts;
        mapping(address => Vote) votes;
        address[] voters;
        bool finalized;
    }

    // State variables
    mapping(bytes32 => VotingSession) public sessions;
    mapping(bytes32 => Vote) public votes;
    mapping(address => bool) public authorizedValidators;

    address public owner;
    uint256 public sessionCount;

    // Modifiers
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }

    modifier onlyAuthorizedValidator() {
        require(authorizedValidators[msg.sender] || msg.sender == owner, "Not authorized validator");
        _;
    }

    modifier sessionExists(bytes32 sessionId) {
        require(sessions[sessionId].creator != address(0), "Session does not exist");
        _;
    }

    modifier sessionActive(bytes32 sessionId) {
        VotingSession storage session = sessions[sessionId];
        require(block.timestamp >= session.startTime && block.timestamp <= session.endTime, "Session not active");
        require(!session.finalized, "Session already finalized");
        _;
    }

    constructor() {
        owner = msg.sender;
        authorizedValidators[msg.sender] = true;
    }

    /**
     * @dev Create a new voting session
     */
    function createSession(
        string memory title,
        bytes32[] memory options,
        uint256 durationMinutes,
        uint256 minParticipants,
        uint256 consensusThreshold
    ) external returns (bytes32) {
        require(options.length >= 2, "At least 2 options required");
        require(consensusThreshold > 0 && consensusThreshold <= 100, "Invalid consensus threshold");
        require(durationMinutes > 0, "Duration must be positive");

        sessionCount++;
        bytes32 sessionId = keccak256(abi.encodePacked(
            msg.sender,
            title,
            block.timestamp,
            sessionCount
        ));

        VotingSession storage session = sessions[sessionId];
        session.sessionId = sessionId;
        session.creator = msg.sender;
        session.title = title;
        session.options = options;
        session.startTime = block.timestamp;
        session.endTime = block.timestamp + (durationMinutes * 1 minutes);
        session.minParticipants = minParticipants;
        session.consensusThreshold = consensusThreshold;
        session.status = ValidationResult.PENDING;
        session.finalized = false;

        return sessionId;
    }

    /**
     * @dev Cast an on-chain vote
     */
    function castOnChainVote(bytes32 sessionId, bytes32 optionId)
        external
        sessionExists(sessionId)
        sessionActive(sessionId)
    {
        VotingSession storage session = sessions[sessionId];

        // Check if voter already voted
        require(session.votes[msg.sender].voter == address(0), "Already voted");

        // Validate option exists
        bool validOption = false;
        for (uint256 i = 0; i < session.options.length; i++) {
            if (session.options[i] == optionId) {
                validOption = true;
                break;
            }
        }
        require(validOption, "Invalid option");

        // Create vote
        bytes32 voteId = keccak256(abi.encodePacked(
            msg.sender,
            sessionId,
            optionId,
            block.timestamp
        ));

        Vote memory newVote = Vote({
            voteId: voteId,
            voter: msg.sender,
            sessionId: sessionId,
            optionId: optionId,
            timestamp: block.timestamp,
            voteType: VoteType.ON_CHAIN,
            signature: "",
            isValid: true
        });

        votes[voteId] = newVote;
        session.votes[msg.sender] = newVote;
        session.voters.push(msg.sender);
        session.voteCounts[optionId]++;

        emit VoteRecorded(voteId, msg.sender, sessionId, block.timestamp);

        // Check if consensus reached
        _checkConsensus(sessionId);
    }

    /**
     * @dev Submit off-chain vote for validation
     */
    function submitOffChainVote(
        bytes32 sessionId,
        bytes32 optionId,
        bytes memory signature,
        bytes32 voteHash
    ) external sessionExists(sessionId) sessionActive(sessionId) {
        VotingSession storage session = sessions[sessionId];

        // Check if voter already voted
        require(session.votes[msg.sender].voter == address(0), "Already voted");

        // Create vote ID
        bytes32 voteId = keccak256(abi.encodePacked(
            msg.sender,
            sessionId,
            voteHash,
            block.timestamp
        ));

        Vote memory newVote = Vote({
            voteId: voteId,
            voter: msg.sender,
            sessionId: sessionId,
            optionId: optionId,
            timestamp: block.timestamp,
            voteType: VoteType.OFF_CHAIN_PENDING,
            signature: signature,
            isValid: false // Will be validated separately
        });

        votes[voteId] = newVote;
        session.votes[msg.sender] = newVote;
        session.voters.push(msg.sender);

        emit VoteRecorded(voteId, msg.sender, sessionId, block.timestamp);
    }

    /**
     * @dev Validate off-chain vote (called by authorized validators)
     */
    function validateOffChainVote(bytes32 voteId, bool isValid)
        external
        onlyAuthorizedValidator
    {
        require(votes[voteId].voter != address(0), "Vote does not exist");

        Vote storage vote = votes[voteId];
        require(vote.voteType == VoteType.OFF_CHAIN_PENDING, "Vote not pending validation");

        vote.isValid = isValid;
        if (isValid) {
            vote.voteType = VoteType.OFF_CHAIN_VERIFIED;
            VotingSession storage session = sessions[vote.sessionId];
            session.voteCounts[vote.optionId]++;

            // Check consensus
            _checkConsensus(vote.sessionId);
        }
    }

    /**
     * @dev Internal function to check if consensus is reached
     */
    function _checkConsensus(bytes32 sessionId) internal {
        VotingSession storage session = sessions[sessionId];

        uint256 totalValidVotes = 0;
        bytes32 winningOption;
        uint256 maxVotes = 0;
        bool hasTie = false;

        // Count valid votes
        for (uint256 i = 0; i < session.voters.length; i++) {
            Vote memory vote = session.votes[session.voters[i]];
            if (vote.isValid) {
                totalValidVotes++;
            }
        }

        // Find winning option
        for (uint256 i = 0; i < session.options.length; i++) {
            uint256 voteCount = session.voteCounts[session.options[i]];
            if (voteCount > maxVotes) {
                maxVotes = voteCount;
                winningOption = session.options[i];
                hasTie = false;
            } else if (voteCount == maxVotes && voteCount > 0) {
                hasTie = true;
            }
        }

        // Check consensus conditions
        if (totalValidVotes >= session.minParticipants) {
            if (hasTie) {
                session.status = ValidationResult.TIED;
            } else {
                uint256 consensusPercentage = (maxVotes * 100) / totalValidVotes;
                if (consensusPercentage >= session.consensusThreshold) {
                    session.status = ValidationResult.VALID;
                    emit ConsensusReached(sessionId, winningOption, consensusPercentage);
                }
            }
        }
    }

    /**
     * @dev Finalize voting session
     */
    function finalizeSession(bytes32 sessionId)
        external
        sessionExists(sessionId)
    {
        VotingSession storage session = sessions[sessionId];
        require(msg.sender == session.creator || msg.sender == owner, "Not authorized");
        require(block.timestamp > session.endTime, "Session still active");
        require(!session.finalized, "Already finalized");

        session.finalized = true;

        emit SessionValidated(sessionId, session.status, session.voters.length);
    }

    /**
     * @dev Get session results
     */
    function getSessionResults(bytes32 sessionId)
        external
        view
        sessionExists(sessionId)
        returns (
            ValidationResult status,
            bytes32[] memory options,
            uint256[] memory voteCounts,
            uint256 totalVotes,
            bool finalized
        )
    {
        VotingSession storage session = sessions[sessionId];

        uint256[] memory counts = new uint256[](session.options.length);
        for (uint256 i = 0; i < session.options.length; i++) {
            counts[i] = session.voteCounts[session.options[i]];
        }

        return (
            session.status,
            session.options,
            counts,
            session.voters.length,
            session.finalized
        );
    }

    /**
     * @dev Add authorized validator
     */
    function addValidator(address validator) external onlyOwner {
        authorizedValidators[validator] = true;
    }

    /**
     * @dev Remove authorized validator
     */
    function removeValidator(address validator) external onlyOwner {
        require(validator != owner, "Cannot remove owner");
        authorizedValidators[validator] = false;
    }

    /**
     * @dev Verify vote signature (helper function)
     */
    function verifyVoteSignature(
        address voter,
        bytes32 sessionId,
        bytes32 optionId,
        uint256 timestamp,
        bytes memory signature
    ) external pure returns (bool) {
        bytes32 messageHash = keccak256(abi.encodePacked(
            voter,
            sessionId,
            optionId,
            timestamp
        ));

        bytes32 ethSignedMessageHash = keccak256(abi.encodePacked(
            "\x19Ethereum Signed Message:\n32",
            messageHash
        ));

        return recoverSigner(ethSignedMessageHash, signature) == voter;
    }

    /**
     * @dev Recover signer from signature
     */
    function recoverSigner(bytes32 ethSignedMessageHash, bytes memory signature)
        internal
        pure
        returns (address)
    {
        require(signature.length == 65, "Invalid signature length");

        bytes32 r;
        bytes32 s;
        uint8 v;

        assembly {
            r := mload(add(signature, 32))
            s := mload(add(signature, 64))
            v := byte(0, mload(add(signature, 96)))
        }

        return ecrecover(ethSignedMessageHash, v, r, s);
    }
}
